const form = document.querySelector("#lookup-form");
const queryInput = document.querySelector("#query");
const charCount = document.querySelector("#char-count");
const submitButton = document.querySelector("#submit-button");
const statusText = document.querySelector("#status");
const result = document.querySelector("#result");
const historyList = document.querySelector("#history-list");
const refreshHistory = document.querySelector("#refresh-history");
const historySearch = document.querySelector("#history-search");
const typeFilter = document.querySelector(".type-filter");
const copyResult = document.querySelector("#copy-result");
let selectedLookupId = null;
let selectedLookup = null;
let selectedType = "";
let pendingDeleteId = null;
let searchTimer = null;

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
  selectedLookupId = null;
  selectedLookup = null;
  result.textContent = message;
  result.className = "result empty";
}

function renderLookup(item) {
  selectedLookupId = item.id;
  selectedLookup = item;
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

    const actions = document.createElement("span");
    actions.className = "history-actions";

    const regenerate = document.createElement("button");
    regenerate.type = "button";
    regenerate.textContent = "重新生成";
    regenerate.addEventListener("click", async (event) => {
      event.stopPropagation();
      await regenerateLookup(item.id);
    });

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "danger-button";
    remove.textContent = pendingDeleteId === item.id ? "确认删除" : "删除";
    remove.addEventListener("click", async (event) => {
      event.stopPropagation();
      await deleteLookup(item.id);
    });

    actions.append(regenerate, remove);
    button.append(title, meta, actions);
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
  const items = await fetchHistoryItems();
  renderHistory(items);
}

async function fetchHistoryItems() {
  const params = new URLSearchParams();
  const q = historySearch.value.trim();
  if (q) {
    params.set("q", q);
  }
  if (selectedType) {
    params.set("query_type", selectedType);
  }
  const url = params.toString() ? `/api/lookups?${params}` : "/api/lookups";
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "读取历史记录失败。");
  }
  return data.items ?? [];
}

async function deleteLookup(id) {
  if (pendingDeleteId !== id) {
    pendingDeleteId = id;
    setStatus("再次点击确认删除");
    renderHistory(await fetchHistoryItems());
    return;
  }

  setStatus("正在删除");
  const response = await fetch(`/api/lookups/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const data = await response.json();
    renderError(data.detail || "删除失败。");
    setStatus("删除失败");
    return;
  }

  if (selectedLookupId === id) {
    renderEmpty("解释结果会显示在这里。");
  }
  pendingDeleteId = null;
  setStatus("已删除");
  await loadHistory();
}

async function regenerateLookup(id) {
  setStatus("正在重新生成");
  const response = await fetch(`/api/lookups/${id}/regenerate`, {
    method: "POST",
  });
  const data = await response.json();
  if (!response.ok) {
    renderError(data.detail || "重新生成失败。");
    setStatus("重新生成失败");
    return;
  }

  queryInput.value = data.original;
  updateCount();
  renderLookup(data);
  setStatus("已重新生成");
  await loadHistory();
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

historySearch.addEventListener("input", () => {
  pendingDeleteId = null;
  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(() => {
    loadHistory().catch((error) => {
      renderError(error.message);
    });
  }, 220);
});

typeFilter.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) {
    return;
  }

  selectedType = button.dataset.type;
  pendingDeleteId = null;
  for (const item of typeFilter.querySelectorAll("button")) {
    item.classList.toggle("active", item === button);
  }
  loadHistory().catch((error) => {
    renderError(error.message);
  });
});

copyResult.addEventListener("click", async () => {
  if (!selectedLookup) {
    setStatus("没有可复制的解释");
    return;
  }

  const examples = selectedLookup.examples
    .map((example) => `- ${example.english}\n  ${example.chinese}`)
    .join("\n");
  const text = [
    selectedLookup.original,
    selectedLookup.pronunciation,
    selectedLookup.explanation,
    examples,
  ]
    .filter(Boolean)
    .join("\n\n");

  try {
    await navigator.clipboard.writeText(text);
    setStatus("已复制");
  } catch {
    renderError("复制失败，请手动选择文本。");
    setStatus("复制失败");
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
