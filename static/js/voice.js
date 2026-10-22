/**
 * HotSeat AI — Web Speech API Voice Output (TTS) & Microphone Dictation
 * =====================================================================
 */

let ttsEnabled = true;
let isRecording = false;
let recognition = null;

function toggleTTS() {
  ttsEnabled = !ttsEnabled;
  const btn = document.getElementById('ttsToggleBtn');
  if (btn) {
    btn.textContent = ttsEnabled ? 'Voice Output: On' : 'Voice Output: Off';
  }
  if (!ttsEnabled && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
}

function speakVCResponse(text) {
  if (!ttsEnabled || !window.speechSynthesis || !text) return;
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.02;
  utterance.pitch = 0.96;
  utterance.volume = 1.0;

  const voices = window.speechSynthesis.getVoices
    ? window.speechSynthesis.getVoices()
    : [];
  const englishVoices = voices.filter((v) => /^en(-|_|$)/i.test(v.lang));
  const preferredVoice =
    englishVoices.find((v) =>
      /natural|neural|google|daniel|alex|samantha|premium/i.test(v.name)
    ) ||
    englishVoices[0] ||
    null;
  if (preferredVoice) {
    utterance.voice = preferredVoice;
  }

  window.speechSynthesis.speak(utterance);
}

const speak = speakVCResponse;

function toggleMic() {
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  const micBtn = document.getElementById('micBtn');

  if (isRecording) {
    isRecording = false;
    micBtn.classList.remove('mic-recording');
    micBtn.textContent = 'Dictate';
    if (recognition) recognition.stop();
    return;
  }

  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    appendChat('system', 'Speech recognition is not supported in this browser.');
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onresult = (event) => {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    let transcript = '';
    for (const result of event.results) {
      transcript += result[0].transcript;
    }
    document.getElementById('userInput').value = transcript;
  };

  recognition.onend = () => {
    isRecording = false;
    micBtn.classList.remove('mic-recording');
    micBtn.textContent = 'Dictate';
  };

  recognition.onerror = (e) => {
    isRecording = false;
    micBtn.classList.remove('mic-recording');
    micBtn.textContent = 'Dictate';
    if (e.error !== 'no-speech' && e.error !== 'aborted') {
      appendChat('system', `Microphone error: ${e.error}`);
    }
  };

  recognition.start();
  isRecording = true;
  micBtn.classList.add('mic-recording');
  micBtn.textContent = 'Stop';
}
