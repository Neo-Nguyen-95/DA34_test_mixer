from playwright.sync_api import sync_playwright, Error
import re


TARGET = "https://mathtiad.vn/"


with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--auto-open-devtools-for-tabs"],
    )

    context = browser.new_context()

    # ============================================================
    # PATCH MAIN JS
    # ============================================================

    def patch_js(route):
        response = route.fetch()
        body = response.text()
        original = body

        # ------------------------------------------
        # Disable anti-devtools
        # ------------------------------------------

        body = body.replace(
            'detectors:"all"',
            'detectors:[]'
        )

        body = body.replace(
            'ondevtoolopen:(e,t)=>{window.location.href="https://www.google.com"}',
            'ondevtoolopen:(e,t)=>{}'
        )

        # ------------------------------------------
        # Log decrypted API response
        # ------------------------------------------

        old = 'return JSON.parse((new TextDecoder).decode(r))'

        new = '''
        const __dpad_plaintext=(new TextDecoder).decode(r);
        const __dpad_json=JSON.parse(__dpad_plaintext);

        window.__DPAD_DECRYPTED__ = window.__DPAD_DECRYPTED__ || [];

        window.__DPAD_DECRYPTED__.push({
            time: new Date().toISOString(),
            keyId: e.keyId,
            requestId: e.requestId,
            data: __dpad_json
        });

        window.__DPAD_LAST_RESPONSE__ = __dpad_json;

        console.warn(
            "[DPAD DECRYPTED]",
            e.requestId,
            __dpad_json
        );

        return __dpad_json
        '''

        if old in body:
            body = body.replace(old, new)
            print("PATCHED decrypted-response capture")
        else:
            print("WARNING: decrypt pattern not found")

        print("Modified:", body != original)

        headers = dict(response.headers)

        for key in list(headers):
            if key.lower() in {
                "content-encoding",
                "content-length",
                "transfer-encoding",
                "etag",
            }:
                headers.pop(key, None)

        headers["content-type"] = "application/javascript; charset=utf-8"

        route.fulfill(
            status=response.status,
            headers=headers,
            body=body,
        )

    context.route(
        re.compile(
            r"https://mathtiad\.vn/static/js/main\..*\.js"
        ),
        patch_js,
    )

    page = context.new_page()

    # ============================================================
    # REQUEST
    # ============================================================

    def on_request(request):
        if "mathtiad.vn" in request.url:
            print(
                ">>>",
                request.resource_type.upper(),
                request.method,
                request.url,
            )

    page.on("request", on_request)

    # ============================================================
    # RESPONSE
    # ============================================================

    def on_response(response):
        if "/api/v2/question-bank/user" not in response.url:
            return

        print("\n" + "=" * 100)
        print("QUESTION BANK RESPONSE")
        print("URL:", response.url)
        print("STATUS:", response.status)

        print("\nHEADERS:")
        for k, v in response.headers.items():
            print(f"{k}: {v}")

        try:
            raw = response.body()

            print("\nRAW BODY SIZE:", len(raw))
            print("FIRST 200 BYTES:")
            print(raw[:200])

            with open("tiad_question_response.bin", "wb") as f:
                f.write(raw)

            try:
                text = raw.decode("utf-8")

                print("\nUTF-8 BODY:")
                print(text[:5000])

                with open(
                    "tiad_question_response.txt",
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(text)

            except UnicodeDecodeError:
                print("\nBody is not UTF-8 text.")

        except Exception as e:
            print("Cannot read body:", repr(e))


    page.on("response", on_response)

    # ============================================================
    # FAILED REQUEST
    # ============================================================

    def on_failed(request):
        if "mathtiad.vn" in request.url:
            print(
                "XXX FAILED:",
                request.url,
                request.failure,
            )

    page.on("requestfailed", on_failed)

    # ============================================================
    # CONSOLE
    # ============================================================

    def on_console(msg):
        print(
            f"[CONSOLE {msg.type.upper()}]",
            msg.text
        )

    page.on("console", on_console)

    # ============================================================
    # JAVASCRIPT ERRORS
    # ============================================================

    def on_page_error(error):
        print("\n" + "!" * 100)
        print("JAVASCRIPT ERROR")
        print(error)
        print("!" * 100 + "\n")

    page.on("pageerror", on_page_error)

    # ============================================================
    # NAVIGATION
    # ============================================================

    def on_navigation(frame):
        if frame == page.main_frame:
            print(
                "NAVIGATED:",
                frame.url
            )

    page.on(
        "framenavigated",
        on_navigation,
    )

    # ============================================================
    # OPEN PAGE
    # ============================================================

    print("\nOpening:", TARGET)

    try:
        page.goto(
            TARGET,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

    except Exception as e:
        print("goto error:", repr(e))

    print("\nCurrent URL:", page.url)

    # ============================================================
    # QUAN TRỌNG:
    # KHÔNG dùng input() vì nó block Playwright event loop.
    # ============================================================

    print("\nBrowser đang chạy.")
    print("Bạn có thể thao tác với DevTools.")
    print("Terminal sẽ tiếp tục ghi request/response.")
    print("Nhấn Ctrl+C trong terminal để kết thúc.\n")

    try:
        while True:
            # Giữ Playwright event loop hoạt động
            page.wait_for_timeout(1000)

    except KeyboardInterrupt:
        print("\nStopping...")

    except Error as e:
        print("\nBrowser/page closed:", e)

    finally:
        browser.close()