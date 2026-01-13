const terminalElement = document.getElementById("terminal");
const term = new Terminal({
  cursorBlink: true,
  fontFamily: "Menlo, Monaco, Consolas, 'Courier New', monospace",
  fontSize: 14,
  theme: {
    background: "#101820",
    foreground: "#d8dee9",
  },
});

const fitAddon = new FitAddon.FitAddon();
term.loadAddon(fitAddon);
term.open(terminalElement);
fitAddon.fit();

const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
const wsHost = `${wsProtocol}://${window.location.hostname}:8765`;
const socket = new WebSocket(wsHost);

const resizeObserver = new ResizeObserver(() => {
  fitAddon.fit();
  sendResize();
});
resizeObserver.observe(terminalElement);

function sendResize() {
  const dimensions = fitAddon.proposeDimensions();
  if (!dimensions) {
    return;
  }
  socket.send(
    JSON.stringify({
      type: "resize",
      cols: dimensions.cols,
      rows: dimensions.rows,
    })
  );
}

socket.addEventListener("open", () => {
  term.focus();
  sendResize();
});

socket.addEventListener("message", (event) => {
  term.write(event.data);
});

socket.addEventListener("close", () => {
  term.write("\r\n[connection closed]\r\n");
});

term.onData((data) => {
  socket.send(JSON.stringify({ type: "input", data }));
});
