const form = document.querySelector('#chat-form');
const input = document.querySelector('#message');
const messages = document.querySelector('#messages');
const mode = document.querySelector('#mode');

function addMessage(text, role, escalated = false) {
  const node = document.createElement('div');
  node.className = `message ${role}${escalated ? ' escalated' : ''}`;
  node.textContent = text;
  messages.appendChild(node);
  messages.scrollTop = messages.scrollHeight;
  return node;
}

async function sendQuestion(question) {
  addMessage(question, 'user');
  const pending = addMessage('Проверяю базу знаний…', 'assistant');
  try {
    const response = await fetch('/api/chat', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: question})
    });
    if (!response.ok) throw new Error('Ошибка сервера');
    const data = await response.json();
    pending.remove();
    addMessage(data.answer, 'assistant', data.escalation);
  } catch (error) {
    pending.textContent = 'Не удалось получить ответ. Проверьте запуск сервера и повторите попытку.';
    pending.classList.add('escalated');
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  input.value = '';
  await sendQuestion(question);
});

document.querySelectorAll('[data-question]').forEach(button => button.addEventListener('click', () => sendQuestion(button.dataset.question)));

fetch('/api/health').then(r => r.json()).then(data => {
  mode.textContent = data.openai_enabled ? 'OpenAI подключён' : 'Демо-режим';
});

fetch('/api/checklists').then(r => r.json()).then(groups => {
  const container = document.querySelector('#checklists');
  Object.entries(groups).forEach(([name, items]) => {
    if (!items.length) return;
    const group = document.createElement('section');
    group.className = 'checklist-group';
    const heading = document.createElement('h3'); heading.textContent = name; group.appendChild(heading);
    items.forEach(item => {
      const label = document.createElement('label'); label.className = 'check-item';
      const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.checked = localStorage.getItem(item.id) === '1';
      checkbox.addEventListener('change', () => localStorage.setItem(item.id, checkbox.checked ? '1' : '0'));
      const span = document.createElement('span'); span.textContent = item.task;
      label.append(checkbox, span); group.appendChild(label);
    });
    container.appendChild(group);
  });
});

