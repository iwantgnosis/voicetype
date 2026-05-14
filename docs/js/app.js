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

const pill = document.getElementById("pill-widget");
const pillLabel = document.getElementById("pill-label");
const typedText = document.getElementById("typed-text");

const demoText = "voice type is ready and working";

const states = [
  { cls: "done", label: "I am ready", duration: 2200 },
  { cls: "", label: "Ready", duration: 1400 },
  { cls: "listening", label: "Listening...", duration: 2800 },
  { cls: "processing", label: "Processing...", duration: 1700 },
  { cls: "done", label: "Inserted", duration: 2200 },
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
    charIndex += 1;
  } else if (typeInterval) {
    clearInterval(typeInterval);
    typeInterval = null;
  }
}

function runDemo() {
  const state = states[stateIndex];

  clearPillState();
  if (state.cls) {
    pill.classList.add(state.cls);
  }
  pillLabel.textContent = state.label;

  if (state.label === "I am ready") {
    charIndex = 0;
    typedText.textContent = "";
  }

  if (state.label === "Inserted" && charIndex === 0 && !typeInterval) {
    typeInterval = setInterval(typeText, 55);
  }

  stateIndex = (stateIndex + 1) % states.length;
  setTimeout(runDemo, state.duration);
}

setTimeout(runDemo, 1200);

const nav = document.getElementById("nav");
window.addEventListener("scroll", () => {
  if (window.scrollY > 40) {
    nav.style.background = "rgba(6, 9, 14, 0.95)";
  } else {
    nav.style.background = "rgba(6, 9, 14, 0.8)";
  }
});
