from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HOST = "127.0.0.1"
PORT = 8000


PAGE = """<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>Welcome to Hackday</title> 
	<style>
		:root {
			--ink: #17324d;
			--muted: #58728b;
			--paper: #f7f3ea;
			--mint: #b9e6d1;
			--coral: #ff765e;
			--sun: #ffd166;
		}

		* { box-sizing: border-box; }
		body {
			margin: 0;
			min-height: 100vh;
			overflow-x: hidden;
			color: var(--ink);
			background: var(--paper);
			font-family: Georgia, "Times New Roman", serif;
		}

		.page {
			position: relative;
			display: grid;
			min-height: 100vh;
			place-items: center;
			padding: 3rem 1.5rem;
			isolation: isolate;
			background:
				radial-gradient(circle at 15% 20%, rgba(185, 230, 209, .8), transparent 26rem),
				radial-gradient(circle at 90% 85%, rgba(255, 209, 102, .52), transparent 24rem);
		}

		.grain {
			position: absolute;
			inset: 0;
			z-index: -1;
			opacity: .24;
			background-image: radial-gradient(rgba(23, 50, 77, .22) .7px, transparent .7px);
			background-size: 9px 9px;
			pointer-events: none;
		}

		.orbit, .orbit::after {
			position: absolute;
			border: 1px solid rgba(23, 50, 77, .18);
			border-radius: 50%;
			content: "";
			pointer-events: none;
		}
		.orbit { width: 28rem; height: 28rem; right: -10rem; top: -12rem; animation: drift 14s ease-in-out infinite; }
		.orbit::after { width: 19rem; height: 19rem; left: 3rem; top: 3rem; }

		.welcome {
			width: min(100%, 960px);
			padding: clamp(2rem, 6vw, 5rem);
			border: 1px solid rgba(23, 50, 77, .15);
			background: rgba(255, 255, 255, .53);
			box-shadow: 18px 18px 0 rgba(23, 50, 77, .08);
			animation: arrive .9s cubic-bezier(.2, .8, .2, 1) both;
		}

		.eyebrow {
			display: flex;
			align-items: center;
			gap: .7rem;
			margin: 0 0 2rem;
			color: var(--coral);
			font: 700 .78rem/1.2 Arial, sans-serif;
			letter-spacing: .16em;
			text-transform: uppercase;
		}
		.eyebrow::before { width: 2.5rem; height: 2px; background: var(--coral); content: ""; }
		h1 { max-width: 750px; margin: 0; font-size: clamp(3.7rem, 11vw, 8.7rem); line-height: .86; letter-spacing: -.07em; font-weight: 400; }
		h1 span { display: inline-block; color: var(--coral); animation: wave 3.8s ease-in-out infinite; transform-origin: 70% 80%; }
		.intro { max-width: 520px; margin: 2rem 0 2.5rem; color: var(--muted); font-size: clamp(1.05rem, 2vw, 1.3rem); line-height: 1.55; }
		.actions { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem; }
		button {
			border: 0;
			padding: .95rem 1.25rem;
			color: #fff;
			background: var(--ink);
			font: 700 .86rem Arial, sans-serif;
			cursor: pointer;
			transition: transform .2s ease, background .2s ease;
		}
		button:hover, button:focus-visible { background: var(--coral); transform: translateY(-3px) rotate(-1deg); outline: none; }
		.note { color: var(--muted); font: .76rem Arial, sans-serif; letter-spacing: .04em; }
		.spark { position: absolute; width: 13px; height: 13px; background: var(--sun); animation: twinkle 2.4s ease-in-out infinite; }
		.spark.one { left: 9%; top: 35%; transform: rotate(45deg); }
		.spark.two { right: 15%; bottom: 18%; width: 9px; height: 9px; animation-delay: .8s; }

		@keyframes arrive { from { opacity: 0; transform: translateY(28px) scale(.97); } to { opacity: 1; transform: none; } }
		@keyframes wave { 0%, 100% { transform: rotate(0); } 50% { transform: rotate(5deg) translateY(-3px); } }
		@keyframes drift { 50% { transform: translate(-25px, 20px) rotate(8deg); } }
		@keyframes twinkle { 0%, 100% { opacity: .35; transform: scale(.8) rotate(45deg); } 50% { opacity: 1; transform: scale(1.3) rotate(135deg); } }
		@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; } }
		@media (max-width: 600px) { .welcome { box-shadow: 9px 9px 0 rgba(23, 50, 77, .08); } .orbit { right: -17rem; } }
	</style>
</head>
<body>
	<main class="page">
		<div class="grain" aria-hidden="true"></div>
		<div class="orbit" aria-hidden="true"></div>
		<div class="spark one" aria-hidden="true"></div>
		<div class="spark two" aria-hidden="true"></div>
		<section class="welcome" aria-labelledby="welcome-title">
			<p class="eyebrow">Hackday 1.0 · Decodep Community</p>
			<h1 id="welcome-title">Make room for <span>good</span> ideas.</h1>
			<p class="intro">A small beginning for bold experiments, thoughtful teamwork, and the next thing worth building.</p>
			<div class="actions">
				<button id="begin" type="button">Begin exploring <span aria-hidden="true">→</span></button>
				<span class="note" id="status">Your canvas is ready.</span>
			</div>
		</section>
	</main>
	<script>
		const begin = document.querySelector('#begin');
		const status = document.querySelector('#status');
		begin.addEventListener('click', () => {
			status.textContent = 'Let’s make something memorable.';
			begin.textContent = 'Let’s go →';
			begin.animate([{ transform: 'scale(1)' }, { transform: 'scale(1.06)' }, { transform: 'scale(1)' }], { duration: 420, easing: 'ease-out' });
		});
	</script>
</body>
</html>"""


class WelcomeHandler(BaseHTTPRequestHandler):
		def do_GET(self):
				if self.path != "/":
						self.send_error(404)
						return
				content = PAGE.encode("utf-8")
				self.send_response(200)
				self.send_header("Content-Type", "text/html; charset=utf-8")
				self.send_header("Content-Length", str(len(content)))
				self.end_headers()
				self.wfile.write(content)

		def log_message(self, format, *args):
				return


if __name__ == "__main__":
		server = ThreadingHTTPServer((HOST, PORT), WelcomeHandler)
		print(f"Welcome app running at http://{HOST}:{PORT}")
		try:
				server.serve_forever()
		except KeyboardInterrupt:
				print("\nWelcome app stopped.")
		finally:
				server.server_close()