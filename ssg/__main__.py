"""Command-line interface for ssg: build and preview a static site."""
import argparse
import datetime
import functools
import http.server
import os
import re
import sys
import threading

from .build import build_site
from .config import ConfigError, load_config
from .watch import watch_loop

DEFAULT_SITE_DIR = "site"


def _slugify(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "untitled"


def cmd_build(args):
    site_dir = args.site
    try:
        _apply_config(args)
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    content_dir = os.path.join(site_dir, "content")
    templates_dir = os.path.join(site_dir, "templates")
    static_dir = os.path.join(site_dir, "static")
    output_dir = args.output or os.path.join(site_dir, "_build")

    if not os.path.isdir(content_dir):
        print(f"error: no content directory at {content_dir}", file=sys.stderr)
        return 1

    pages = build_site(content_dir, templates_dir, output_dir, static_dir, args.title,
                        args.base_url, args.drafts, args.page_size)
    print(f"Built {len(pages)} page(s) into {output_dir}")
    if args.base_url:
        print(f"Wrote feed.xml (base URL: {args.base_url})")
    return 0


def cmd_new(args):
    site_dir = args.site
    posts_dir = os.path.join(site_dir, "content", "posts")
    os.makedirs(posts_dir, exist_ok=True)
    slug = _slugify(args.title)
    path = os.path.join(posts_dir, f"{slug}.md")
    if os.path.exists(path):
        print(f"error: {path} already exists", file=sys.stderr)
        return 1
    today = datetime.date.today().isoformat()
    draft_line = "draft: true\n" if args.draft else ""
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"---\ntitle: {args.title}\ndate: {today}\n{draft_line}---\n\nWrite here.\n")
    print(f"Created {path}")
    return 0


def cmd_watch(args):
    site_dir = args.site
    try:
        _apply_config(args)
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    content_dir = os.path.join(site_dir, "content")
    templates_dir = os.path.join(site_dir, "templates")
    static_dir = os.path.join(site_dir, "static")
    output_dir = args.output or os.path.join(site_dir, "_build")

    if not os.path.isdir(content_dir):
        print(f"error: no content directory at {content_dir}", file=sys.stderr)
        return 1

    def on_build(pages):
        print(f"Built {len(pages)} page(s) into {output_dir}")

    print(f"Watching {content_dir}, {templates_dir}, {static_dir} for changes (Ctrl+C to stop)")
    try:
        watch_loop(content_dir, templates_dir, output_dir, static_dir, args.title,
                   args.base_url, args.drafts, args.page_size, poll_interval=args.interval,
                   on_build=on_build)
    except KeyboardInterrupt:
        pass
    return 0


def cmd_serve(args):
    site_dir = args.site
    try:
        _apply_config(args)
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    output_dir = args.output or os.path.join(site_dir, "_build")
    content_dir = os.path.join(site_dir, "content")
    templates_dir = os.path.join(site_dir, "templates")
    static_dir = os.path.join(site_dir, "static")

    if not os.path.isdir(content_dir):
        print(f"error: no content directory at {content_dir}", file=sys.stderr)
        return 1

    watch_thread = None
    stop_event = threading.Event()
    if args.watch:
        def on_build(pages):
            print(f"Rebuilt {len(pages)} page(s)")

        watch_thread = threading.Thread(
            target=watch_loop,
            args=(content_dir, templates_dir, output_dir, static_dir, args.title,
                  args.base_url, args.drafts, args.page_size),
            kwargs={"poll_interval": args.interval, "stop_event": stop_event,
                    "on_build": on_build},
            daemon=True,
        )
        watch_thread.start()
    else:
        build_site(content_dir, templates_dir, output_dir, static_dir, args.title, args.base_url,
                   args.drafts, args.page_size)

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=output_dir)
    server = http.server.ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving {output_dir} on http://{args.host}:{server.server_port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        server.server_close()
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="ssg", description="A small static site generator")
    parser.add_argument("--site", default=DEFAULT_SITE_DIR, help="site directory (default: site)")
    parser.add_argument("--title", default=None,
                         help="site title for the index page (default: 'My Site', "
                              "or ssg.toml's [site] title)")
    parser.add_argument("--base-url", default=None,
                         help="public site root (e.g. https://example.com); "
                              "if given, also writes feed.xml (default: ssg.toml's "
                              "[site] base_url, if set)")
    parser.add_argument("--drafts", action="store_true", default=None,
                         help="include pages marked 'draft: true' in front matter "
                              "(excluded by default, or by ssg.toml's [site] drafts)")
    parser.add_argument("--page-size", type=int, default=None,
                         help="split the index and each tag's listing page into pages of "
                              "this many entries (default: no pagination, or ssg.toml's "
                              "[site] page_size)")
    sub = parser.add_subparsers(dest="command", required=True)

    build_p = sub.add_parser("build", help="render content into static HTML")
    build_p.add_argument("--output", help="output directory (default: <site>/_build)")
    build_p.set_defaults(func=cmd_build)

    new_p = sub.add_parser("new", help="scaffold a new post")
    new_p.add_argument("title", help="post title")
    new_p.add_argument("--draft", action="store_true", help="mark the new post as a draft")
    new_p.set_defaults(func=cmd_new)

    serve_p = sub.add_parser("serve", help="build and serve the site locally")
    serve_p.add_argument("--output", help="output directory (default: <site>/_build)")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8000)
    serve_p.add_argument("--watch", action="store_true",
                          help="rebuild automatically when source files change")
    serve_p.add_argument("--interval", type=float, default=1.0,
                          help="seconds between change checks with --watch (default: 1.0)")
    serve_p.set_defaults(func=cmd_serve)

    watch_p = sub.add_parser("watch", help="rebuild automatically when source files change")
    watch_p.add_argument("--output", help="output directory (default: <site>/_build)")
    watch_p.add_argument("--interval", type=float, default=1.0,
                          help="seconds between change checks (default: 1.0)")
    watch_p.set_defaults(func=cmd_watch)

    return parser


def _apply_config(args):
    """Fill in unset --title/--base-url/--drafts/--page-size from the site's ssg.toml.

    CLI flags always win; config values win over built-in defaults.
    Raises ConfigError on a malformed ssg.toml.
    """
    config = load_config(args.site).get("site", {})
    if args.title is None:
        args.title = config.get("title", "My Site")
    if args.base_url is None:
        args.base_url = config.get("base_url")
    if args.drafts is None:
        args.drafts = bool(config.get("drafts", False))
    if args.page_size is None:
        args.page_size = config.get("page_size")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
