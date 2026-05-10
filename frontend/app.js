const form = document.querySelector("#lookup-form");
const queryInput = document.querySelector("#query");
const charCount = document.querySelector("#char-count");
const submitButton = document.querySelector("#submit-button");
const statusText = document.querySelector("#status");
const result = document.querySelector("#result");
const historyList = document.querySelector("#history-list");
const refreshHistory = document.querySelector("#refresh-history");

function setStatus(text) {
  statusText.textContent = text;
}

function queryTypeLabel(type) {
  const labels = {
    word: "单词",
    phrase: "短语",
    sentence: "句子",
  };
  return labels[type] || "英文";
}

function formatDate(value) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function renderError(message) {
  result.textContent = message;
  result.className = "result error";
}

function renderEmpty(message) {
  result.textContent = message;
  result.className = "result empty";
}

function renderLookup(item) {
  result.className = "result";
  result.innerHTML = "";

  const title = document.createElement("div");
  title.className = "result-title";

  const original = document.createElement("h3");
  original.textContent = item.original;

  const badge = document.createElement("span");
  badge.className = "badge";
  badge.textContent = queryTypeLabel(item.query_type);

  title.append(original, badge);
  result.append(title);

  if (item.pronunciation) {
    const pronunciation = document.createElement("p");
    pronunciation.className = "pronunciation";
    pronunciation.textContent = item.pronunciation;
    result.append(pronunciation);
  }

  const explanation = document.createElement("p");
  explanation.textContent = item.explanation;
  result.append(explanation);

  if (item.examples?.length) {
    const list = document.createElement("ul");
    list.className = "examples";
    for (const example of item.examples) {
      const entry = document.createElement("li");
      const english = document.createElement("strong");
      english.textContent = example.english;
      const chinese = document.createElement("span");
      chinese.textContent = example.chinese;
      entry.append(english, chinese);
      list.append(entry);
    }
    result.append(list);
  }
}

function renderHistory(items) {
  historyList.innerHTML = "";
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "还没有查询记录。";
    historyList.append(empty);
    return;
  }

  for (const item of items) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "history-item";

    const title = document.createElement("strong");
    title.textContent = item.original;

    const meta = document.createElement("span");
    meta.className = "history-meta";
    meta.innerHTML = `<span>${queryTypeLabel(item.query_type)}</span><span>${formatDate(item.created_at)}</span>`;

    button.append(title, meta);
    button.addEventListener("click", async () => {
      const response = await fetch(`/api/lookups/${item.id}`);
      const detail = await response.json();
      if (!response.ok) {
        renderError(detail.detail || "读取历史记录失败。");
        return;
      }
      queryInput.value = detail.original;
      updateCount();
      renderLookup(detail);
      setStatus("已打开历史记录");
    });
    historyList.append(button);
  }
}

async function loadHistory() {
  const response = await fetch("/api/lookups");
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "读取历史记录失败。");
  }
  renderHistory(data.items ?? []);
}

function updateCount() {
  charCount.textContent = `${queryInput.value.length} / 1200`;
}

queryInput.addEventListener("input", updateCount);

refreshHistory.addEventListener("click", async () => {
  refreshHistory.disabled = true;
  try {
    await loadHistory();
  } catch (error) {
    renderError(error.message);
  } finally {
    refreshHistory.disabled = false;
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = queryInput.value.trim();
  if (!text) {
    queryInput.focus();
    return;
  }

  submitButton.disabled = true;
  setStatus("正在查询");
  renderEmpty("正在生成解释...");

  try {
    const response = await fetch("/api/lookups", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "查询失败。");
    }

    renderLookup(data);
    setStatus("已保存");
    await loadHistory();
  } catch (error) {
    renderError(error.message);
    setStatus("查询失败");
  } finally {
    submitButton.disabled = false;
  }
});

updateCount();
loadHistory().catch(() => {
  renderHistory([]);
});
