/* ═══════════════════════════════════════════════════════════════════
   Voice Typing Assistant — Showcase Interactions
   ═══════════════════════════════════════════════════════════════════ */

// ── Scroll reveal (Intersection Observer) ──────────────────────────
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
      }
    });
  },
  { threshold: 0.15 }
);

document.querySelectorAll(".fade-up").forEach((el) => observer.observe(el));

// ── Interactive pill widget demo ───────────────────────────────────
const pill = document.getElementById("pill-widget");
const pillLabel = document.getElementById("pill-label");
const pillDot = document.getElementById("pill-dot");
const typedText = document.getElementById("typed-text");

const demoText = "AI give me best python project";

const states = [
  { cls: "", label: "Ready", duration: 2000 },
  { cls: "listening", label: "Listening…", duration: 3000 },
  { cls: "processing", label: "Processing…", duration: 1800 },
  { cls: "done", label: "Inserted ✓", duration: 2000 },
];

let stateIndex = 0;
let charIndex = 0;
let typeInterval = null;

function clearPillState() {
  pill.classList.remove("listening", "processing", "done");
}

function typeText() {
  if (charIndex <= demoText.length) {
    typedText.textContent = demoText.substring(0, charIndex);
    charIndex++;
  } else {
    clearInterval(typeInterval);
    typeInterval = null;
  }
}

function runDemo() {
  const state = states[stateIndex];

  clearPillState();
  if (state.cls) pill.classList.add(state.cls);
  pillLabel.textContent = state.label;

  // Start typing when we hit "done" state
  if (state.cls === "done" && charIndex === 0) {
    typeInterval = setInterval(typeText, 55);
  }

  // Reset text when going back to "Ready"
  if (state.cls === "" && stateIndex === 0) {
    charIndex = 0;
    typedText.textContent = "";
  }

  stateIndex = (stateIndex + 1) % states.length;

  setTimeout(runDemo, state.duration);
}

// Start the demo loop after a short delay
setTimeout(runDemo, 1200);

// ── Sticky nav background on scroll ───────────────────────────────
const nav = document.getElementById("nav");
window.addEventListener("scroll", () => {
  if (window.scrollY > 40) {
    nav.style.background = "rgba(6, 9, 14, 0.95)";
  } else {
    nav.style.background = "rgba(6, 9, 14, 0.8)";
  }
});
