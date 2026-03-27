const methodSelect = document.getElementById("methodSelect");
const methodDescription = document.getElementById("methodDescription");
const methodForm = document.getElementById("methodForm");
const runButton = document.getElementById("runButton");
const outputTable = document.getElementById("outputTable");
const statusBadge = document.getElementById("statusBadge");
const chartPanel = document.querySelector(".chart-panel");
const plotlyChart = document.getElementById("plotlyChart");
const plotMessage = document.getElementById("plotMessage");
const latexPreviewBox = document.getElementById("latexPreviewBox");
const latexPreviewMath = document.getElementById("latexPreviewMath");
const latexPreviewError = document.getElementById("latexPreviewError");
const globalIteracionesInput = document.getElementById("globalIteraciones");
const globalToleranciaInput = document.getElementById("globalTolerancia");
const globalPrecisionInput = document.getElementById("globalPrecision");
const globalPorcentajeInput = document.getElementById("globalPorcentaje");
const globalDebugModeInput = document.getElementById("globalDebugMode");
const fixedPointHelpButton = document.getElementById("fixedPointHelpButton");
const fixedPointHelpModal = document.getElementById("fixedPointHelpModal");
const fixedPointHelpBackdrop = document.getElementById("fixedPointHelpBackdrop");
const fixedPointHelpClose = document.getElementById("fixedPointHelpClose");
const fixedPointHelpInput = document.getElementById("fixedPointHelpInput");
const fixedPointHelpSuggest = document.getElementById("fixedPointHelpSuggest");
const fixedPointHelpResult = document.getElementById("fixedPointHelpResult");
const fixedPointHelpPreviewBox = document.getElementById("fixedPointHelpPreviewBox");
const fixedPointHelpPreviewMath = document.getElementById("fixedPointHelpPreviewMath");
const fixedPointHelpPreviewError = document.getElementById("fixedPointHelpPreviewError");

let methods = [];
let latexPreviewTimer = null;
let activeRunId = 0;
let fixedPointSuggestedG = "";
let fixedPointHelpPreviewTimer = null;

const STORAGE_KEY = "metodos_numericos_ui_state_v1";
const EXPRESSION_OPS = [
  { label: "+", insert: "+" },
  { label: "-", insert: "-" },
  { label: "*", insert: "*" },
  { label: "/", insert: "/" },
  { label: "^", insert: "**" },
  { label: "( )", insert: "()", cursorOffset: -1 },
  { label: "sqrt", insert: "sqrt()", cursorOffset: -1 },
  { label: "exp", insert: "exp()", cursorOffset: -1 },
  { label: "sin", insert: "sin()", cursorOffset: -1 },
  { label: "cos", insert: "cos()", cursorOffset: -1 },
  { label: "tan", insert: "tan()", cursorOffset: -1 },
  { label: "log", insert: "log()", cursorOffset: -1 },
  { label: "π", insert: "π" },
];

let persistedState = {
  selectedMethod: null,
  global: {},
  paramsByMethod: {},
};

function setStatus(kind, label) {
  statusBadge.className = `badge ${kind}`;
  statusBadge.textContent = label;
}

function selectedMethod() {
  return methods.find((m) => m.key === methodSelect.value);
}

function isLagrangeMethod(method) {
  return Boolean(method && method.key === "lagrange");
}

function isDiferenciaFinitaMethod(method) {
  return Boolean(method && method.key === "diferencia_finita");
}

function isFixedPointHelperMethod(method) {
  return Boolean(method && ["punto_fijo", "aceleracion_aitken"].includes(method.key));
}

function supportsPlot(method) {
  if (!method) {
    return false;
  }
  return ["newton_raphson", "biseccion", "punto_fijo", "aceleracion_aitken", "lagrange", "diferencia_finita"].includes(method.key);
}

function shouldRenderPlot(method, params = null) {
  if (!supportsPlot(method)) {
    return false;
  }

  if (method?.key === "diferencia_finita") {
    const hasExpression = params
      ? String(params.f_expr || "").trim().length > 0
      : methodForm.dataset.diferenciaFinitaMode !== "images";
    return hasExpression;
  }

  return true;
}

function setPlotMessage(message) {
  plotMessage.textContent = message;
}

function clearPlot() {
  if (window.Plotly && plotlyChart) {
    window.Plotly.purge(plotlyChart);
  }
}

function clearOutput() {
  outputTable.classList.add("output-empty");
  outputTable.textContent = "Todavía no hay resultados. Ejecutá un método para comenzar.";
}

function loadPersistedState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return;
    }
    const parsed = JSON.parse(raw);
    persistedState = {
      selectedMethod: typeof parsed.selectedMethod === "string" ? parsed.selectedMethod : null,
      global: parsed.global && typeof parsed.global === "object" ? parsed.global : {},
      paramsByMethod: parsed.paramsByMethod && typeof parsed.paramsByMethod === "object" ? parsed.paramsByMethod : {},
    };
  } catch {
    persistedState = { selectedMethod: null, global: {}, paramsByMethod: {} };
  }
}

function savePersistedState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(persistedState));
}

function applyPersistedGlobalInputs() {
  const global = persistedState.global || {};
  if (global.iteraciones != null) {
    globalIteracionesInput.value = String(global.iteraciones);
  }
  if (global.toleranciaExp != null) {
    globalToleranciaInput.value = String(global.toleranciaExp);
  } else if (global.tolerancia != null) {
    const legacyTolerance = Number(global.tolerancia);
    if (Number.isFinite(legacyTolerance) && legacyTolerance > 0) {
      const approxExponent = Math.round(-Math.log10(legacyTolerance));
      globalToleranciaInput.value = String(Math.max(0, approxExponent));
    }
  }
  if (global.precision != null) {
    globalPrecisionInput.value = String(global.precision);
  }
  if (global.porcentaje != null) {
    globalPorcentajeInput.value = String(global.porcentaje);
  }
  if (global.debugMode != null) {
    globalDebugModeInput.checked = Boolean(global.debugMode);
  }
}

function persistGlobalInputs() {
  persistedState.global = {
    iteraciones: globalIteracionesInput.value,
    toleranciaExp: globalToleranciaInput.value,
    precision: globalPrecisionInput.value,
    porcentaje: globalPorcentajeInput.value,
    debugMode: globalDebugModeInput.checked,
  };
  savePersistedState();
}

function persistMethodInputs(methodKey) {
  const method = methods.find((item) => item.key === methodKey);
  if (!method) {
    return;
  }

  const values = {};
  for (const field of method.fields) {
    const element = document.getElementById(field.key);
    if (element) {
      values[field.key] = element.value;
    }
  }

  if (methodKey === "lagrange") {
    const previous = persistedState.paramsByMethod[methodKey] || {};
    const mode = methodForm.dataset.lagrangeMode || "expr";
    const next = { ...previous, __lagrange_mode: mode };

    if (mode === "images") {
      next.__lagrange_images = {
        x_nodos: values.x_nodos ?? "",
        y_nodos: values.y_nodos ?? "",
      };
    } else {
      next.__lagrange_expr = {
        f_expr: values.f_expr ?? "",
        x_nodos: values.x_nodos ?? "",
        x_eval: values.x_eval ?? "",
      };
    }

    persistedState.paramsByMethod[methodKey] = next;
    savePersistedState();
    return;
  }

  if (methodKey === "diferencia_finita") {
    const previous = persistedState.paramsByMethod[methodKey] || {};
    const mode = methodForm.dataset.diferenciaFinitaMode || "expr";
    const next = { ...previous, __diferencia_finita_mode: mode };

    if (mode === "images") {
      next.__diferencia_finita_images = {
        x: values.x ?? "",
        h: values.h ?? "",
        metodo: values.metodo ?? "",
        y_xm1: values.y_xm1 ?? "",
        y_x: values.y_x ?? "",
        y_xp1: values.y_xp1 ?? "",
      };
    } else {
      next.__diferencia_finita_expr = {
        f_expr: values.f_expr ?? "",
        x: values.x ?? "",
        h: values.h ?? "",
        metodo: values.metodo ?? "",
      };
    }

    persistedState.paramsByMethod[methodKey] = next;
    savePersistedState();
    return;
  }

  persistedState.paramsByMethod[methodKey] = values;
  savePersistedState();
}

function applyPersistedMethodInputs(methodKey) {
  const methodValues = persistedState.paramsByMethod?.[methodKey];
  if (!methodValues) {
    return;
  }

  if (methodKey === "lagrange") {
    const mode = getPersistedLagrangeMode();
    applyPersistedLagrangeInputsForMode(mode);
    return;
  }

  if (methodKey === "diferencia_finita") {
    const mode = getPersistedDiferenciaFinitaMode();
    applyPersistedDiferenciaFinitaInputsForMode(mode);
    return;
  }

  for (const [fieldKey, value] of Object.entries(methodValues)) {
    const element = document.getElementById(fieldKey);
    if (element) {
      element.value = String(value ?? "");
    }
  }
}

function getLagrangePersistedModePayload(mode) {
  const methodValues = persistedState.paramsByMethod?.lagrange || {};
  const bucketKey = mode === "images" ? "__lagrange_images" : "__lagrange_expr";
  const bucket = methodValues[bucketKey];
  if (bucket && typeof bucket === "object") {
    return bucket;
  }

  // Backward compatibility with legacy flat storage.
  return methodValues;
}

function applyPersistedLagrangeInputsForMode(mode) {
  const payload = getLagrangePersistedModePayload(mode);

  const fExprInput = document.getElementById("f_expr");
  const xNodosInput = document.getElementById("x_nodos");
  const yNodosInput = document.getElementById("y_nodos");
  const xEvalInput = document.getElementById("x_eval");

  if (mode === "images") {
    if (xNodosInput && payload.x_nodos != null) {
      xNodosInput.value = String(payload.x_nodos);
    }
    if (yNodosInput && payload.y_nodos != null) {
      yNodosInput.value = String(payload.y_nodos);
    }
  } else {
    if (fExprInput && payload.f_expr != null) {
      fExprInput.value = String(payload.f_expr);
    }
    if (xNodosInput && payload.x_nodos != null) {
      xNodosInput.value = String(payload.x_nodos);
    }
    if (xEvalInput && payload.x_eval != null) {
      xEvalInput.value = String(payload.x_eval);
    }
  }

  syncHiddenInputsToLagrangeNodeEditor();
}

function getPersistedLagrangeMode() {
  const mode = persistedState.paramsByMethod?.lagrange?.__lagrange_mode;
  return mode === "images" ? "images" : "expr";
}

function getPersistedDiferenciaFinitaMode() {
  const mode = persistedState.paramsByMethod?.diferencia_finita?.__diferencia_finita_mode;
  return mode === "images" ? "images" : "expr";
}

function getDiferenciaFinitaPersistedModePayload(mode) {
  const methodValues = persistedState.paramsByMethod?.diferencia_finita || {};
  const bucketKey = mode === "images" ? "__diferencia_finita_images" : "__diferencia_finita_expr";
  const bucket = methodValues[bucketKey];
  if (bucket && typeof bucket === "object") {
    return bucket;
  }

  // Backward compatibility with legacy flat storage.
  return methodValues;
}

function applyPersistedDiferenciaFinitaInputsForMode(mode) {
  const payload = getDiferenciaFinitaPersistedModePayload(mode);

  const fExprInput = document.getElementById("f_expr");
  const xInput = document.getElementById("x");
  const hInput = document.getElementById("h");
  const metodoInput = document.getElementById("metodo");
  const yXm1Input = document.getElementById("y_xm1");
  const yXInput = document.getElementById("y_x");
  const yXp1Input = document.getElementById("y_xp1");

  if (xInput && payload.x != null) {
    xInput.value = String(payload.x);
  }
  if (hInput && payload.h != null) {
    hInput.value = String(payload.h);
  }
  if (metodoInput && payload.metodo != null) {
    metodoInput.value = String(payload.metodo);
  }

  if (mode === "images") {
    if (yXm1Input && payload.y_xm1 != null) {
      yXm1Input.value = String(payload.y_xm1);
    }
    if (yXInput && payload.y_x != null) {
      yXInput.value = String(payload.y_x);
    }
    if (yXp1Input && payload.y_xp1 != null) {
      yXp1Input.value = String(payload.y_xp1);
    }
  } else {
    if (fExprInput && payload.f_expr != null) {
      fExprInput.value = String(payload.f_expr);
    }
  }
}

function getExpressionInput() {
  const candidates = [document.getElementById("f_expr"), document.getElementById("g_expr")];
  return candidates.find((input) => input && !input.disabled && input.offsetParent !== null) || null;
}

function clearLatexPreview() {
  latexPreviewBox.hidden = true;
  latexPreviewMath.textContent = "\\(\\)";
  latexPreviewError.hidden = true;
  latexPreviewError.textContent = "";
}

function renderMathJax() {
  if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
    window.MathJax.typesetPromise([latexPreviewMath]).catch(() => {});
  }
}

function showLatexPreview(latexText) {
  latexPreviewBox.hidden = false;
  latexPreviewError.hidden = true;
  latexPreviewMath.innerHTML = `\\(${latexText}\\)`;
  renderMathJax();
}

function showLatexError(message) {
  latexPreviewBox.hidden = false;
  latexPreviewMath.textContent = "\\(\\)";
  latexPreviewError.hidden = false;
  latexPreviewError.textContent = message;
}

async function requestLatexPreview(expressionText) {
  const response = await fetch("/api/latex", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ expression: expressionText }),
  });
  const data = await response.json();
  if (!response.ok || !data.success) {
    throw new Error(data.error || "Expresión no válida.");
  }
  return data.latex;
}

function scheduleLatexPreview() {
  const expressionInput = getExpressionInput();
  if (!expressionInput) {
    clearLatexPreview();
    return;
  }

  const text = expressionInput.value.trim();
  if (!text) {
    clearLatexPreview();
    return;
  }

  if (latexPreviewTimer) {
    clearTimeout(latexPreviewTimer);
  }

  latexPreviewTimer = setTimeout(async () => {
    try {
      const latexText = await requestLatexPreview(text);
      showLatexPreview(latexText);
    } catch (error) {
      showLatexError(String(error.message || error));
    }
  }, 220);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function updateFixedPointHelpVisibility(method) {
  if (!fixedPointHelpButton) {
    return;
  }
  fixedPointHelpButton.hidden = true;

  if (!isFixedPointHelperMethod(method)) {
    return;
  }

  const expressionWrapper = methodForm.querySelector('[data-field-key="g_expr"]');
  const expressionInput = document.getElementById("g_expr");
  if (!expressionWrapper || !expressionInput) {
    return;
  }

  let inlineRow = expressionWrapper.querySelector(".fixed-help-inline-row");
  if (!inlineRow) {
    inlineRow = document.createElement("div");
    inlineRow.className = "fixed-help-inline-row";
    expressionWrapper.insertBefore(inlineRow, expressionInput);
    inlineRow.appendChild(expressionInput);
  }

  fixedPointHelpButton.className = "fixed-help-inline-button";
  fixedPointHelpButton.textContent = "!";
  fixedPointHelpButton.title = "Ayuda para construir g(x)";
  fixedPointHelpButton.setAttribute("aria-label", "Ayuda para construir g(x)");
  inlineRow.appendChild(fixedPointHelpButton);
  fixedPointHelpButton.hidden = false;
}

function ensureFixedPointHelpModalToolbar() {
  if (!fixedPointHelpInput) {
    return;
  }

  const container = fixedPointHelpInput.parentElement;
  if (!container) {
    return;
  }

  if (container.querySelector(".fixed-help-expr-ops")) {
    return;
  }

  const toolbar = buildExpressionToolbar(fixedPointHelpInput);
  toolbar.classList.add("fixed-help-expr-ops");
  container.insertBefore(toolbar, fixedPointHelpInput);
}

function closeFixedPointHelpModal() {
  if (!fixedPointHelpModal) {
    return;
  }
  fixedPointHelpModal.hidden = true;
}

function clearFixedPointHelpPreview() {
  if (!fixedPointHelpPreviewBox || !fixedPointHelpPreviewMath || !fixedPointHelpPreviewError) {
    return;
  }
  fixedPointHelpPreviewBox.hidden = true;
  fixedPointHelpPreviewMath.textContent = "\\(\\)";
  fixedPointHelpPreviewError.hidden = true;
  fixedPointHelpPreviewError.textContent = "";
}

function showFixedPointHelpPreview(latexText) {
  if (!fixedPointHelpPreviewBox || !fixedPointHelpPreviewMath || !fixedPointHelpPreviewError) {
    return;
  }
  fixedPointHelpPreviewBox.hidden = false;
  fixedPointHelpPreviewError.hidden = true;
  fixedPointHelpPreviewMath.innerHTML = `\\(${latexText}\\)`;
  if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
    window.MathJax.typesetPromise([fixedPointHelpPreviewMath]).catch(() => {});
  }
}

function showFixedPointHelpPreviewError(message) {
  if (!fixedPointHelpPreviewBox || !fixedPointHelpPreviewMath || !fixedPointHelpPreviewError) {
    return;
  }
  fixedPointHelpPreviewBox.hidden = false;
  fixedPointHelpPreviewMath.textContent = "\\(\\)";
  fixedPointHelpPreviewError.hidden = false;
  fixedPointHelpPreviewError.textContent = message;
}

function scheduleFixedPointHelpPreview() {
  if (!fixedPointHelpInput) {
    return;
  }

  const expressionText = fixedPointHelpInput.value.trim();
  if (!expressionText) {
    clearFixedPointHelpPreview();
    return;
  }

  if (fixedPointHelpPreviewTimer) {
    clearTimeout(fixedPointHelpPreviewTimer);
  }

  fixedPointHelpPreviewTimer = setTimeout(async () => {
    try {
      const latexText = await requestLatexPreview(expressionText);
      showFixedPointHelpPreview(latexText);
    } catch (error) {
      showFixedPointHelpPreviewError(String(error.message || error));
    }
  }, 220);
}

function openFixedPointHelpModal() {
  if (!fixedPointHelpModal || !fixedPointHelpInput || !fixedPointHelpResult) {
    return;
  }
  ensureFixedPointHelpModalToolbar();
  fixedPointHelpModal.hidden = false;
  fixedPointHelpInput.value = "";
  fixedPointSuggestedG = "";
  fixedPointHelpResult.textContent = "Esperando datos...";
  clearFixedPointHelpPreview();
  fixedPointHelpInput.focus();
}

async function suggestFixedPointFunction() {
  if (!fixedPointHelpInput || !fixedPointHelpResult) {
    return;
  }

  const expression = fixedPointHelpInput.value.trim();
  const pointText = (document.getElementById("x")?.value || "").trim();
  if (!expression) {
    fixedPointHelpResult.textContent = "Ingresá la función f(x).";
    return;
  }
  if (!pointText) {
    fixedPointHelpResult.textContent = "Ingresá el valor inicial x para evaluar convergencia.";
    return;
  }

  fixedPointHelpResult.textContent = "Calculando sugerencia...";

  try {
    const response = await fetch("/api/fixed-point/suggest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ expression, point: pointText }),
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.error || "No se pudo generar una sugerencia.");
    }

    fixedPointSuggestedG = String(data.g_expression || "").trim();

    fixedPointHelpResult.innerHTML = `
      <div class="fixed-help-result-row">
        <div class="fixed-help-latex">\\(${escapeHtml(data.g_latex || "")}\\)</div>
        <button type="button" class="fixed-help-copy-icon" title="Copiar al campo principal" aria-label="Copiar al campo principal">📋</button>
      </div>
    `;

    if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
      window.MathJax.typesetPromise([fixedPointHelpResult]).catch(() => {});
    }
  } catch (error) {
    fixedPointSuggestedG = "";
    fixedPointHelpResult.textContent = String(error.message || error);
  }
}

function copySuggestedGToMethodField() {
  const gInput = document.getElementById("g_expr");
  if (!gInput) {
    return;
  }

  if (!fixedPointSuggestedG) {
    return;
  }

  gInput.value = fixedPointSuggestedG;
  gInput.dispatchEvent(new Event("input", { bubbles: true }));
}

function parseTabulateGrid(text) {
  const lines = String(text || "")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  const tableRows = lines
    .filter((line) => line.startsWith("|") && line.endsWith("|"))
    .map((line) => line.split("|").slice(1, -1).map((cell) => cell.trim()));

  if (tableRows.length < 2) {
    return null;
  }

  return { headers: tableRows[0], rows: tableRows.slice(1) };
}

function renderTable(parsed) {
  const headers = parsed.headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("");
  const rows = parsed.rows
    .map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`)
    .join("");

  outputTable.classList.remove("output-empty");
  outputTable.innerHTML = `<table class=\"result-table\"><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table>`;
}

function parseLagrangeSummary(text) {
  const summary = {
    expresionFinal: null,
    expresionFinalLatex: null,
    errorLocal: null,
    errorGlobal: null,
  };

  for (const rawLine of String(text || "").split("\n")) {
    const line = rawLine.trim();
    if (line.startsWith("LAGRANGE_EXPRESION_FINAL:")) {
      summary.expresionFinal = line.replace("LAGRANGE_EXPRESION_FINAL:", "").trim();
      continue;
    }
    if (line.startsWith("LAGRANGE_EXPRESION_FINAL_LATEX:")) {
      summary.expresionFinalLatex = line.replace("LAGRANGE_EXPRESION_FINAL_LATEX:", "").trim();
      continue;
    }
    if (line.startsWith("LAGRANGE_ERROR_LOCAL:")) {
      summary.errorLocal = line.replace("LAGRANGE_ERROR_LOCAL:", "").trim();
      continue;
    }
    if (line.startsWith("LAGRANGE_ERROR_GLOBAL:")) {
      summary.errorGlobal = line.replace("LAGRANGE_ERROR_GLOBAL:", "").trim();
    }
  }

  if (!summary.expresionFinal && !summary.errorLocal && !summary.errorGlobal) {
    return null;
  }
  return summary;
}

function parseDiferenciaFinitaSummary(text) {
  const summary = {
    derivada: null,
    derivadaExacta: null,
    errorAbsoluto: null,
  };

  for (const rawLine of String(text || "").split("\n")) {
    const line = rawLine.trim();
    if (line.startsWith("DIFERENCIA_FINITA_DERIVADA:")) {
      summary.derivada = line.replace("DIFERENCIA_FINITA_DERIVADA:", "").trim();
      continue;
    }
    if (line.startsWith("DIFERENCIA_FINITA_DERIVADA_EXACTA:")) {
      summary.derivadaExacta = line.replace("DIFERENCIA_FINITA_DERIVADA_EXACTA:", "").trim();
      continue;
    }
    if (line.startsWith("DIFERENCIA_FINITA_ERROR_ABSOLUTO:")) {
      summary.errorAbsoluto = line.replace("DIFERENCIA_FINITA_ERROR_ABSOLUTO:", "").trim();
    }
  }

  if (!summary.derivada && !summary.derivadaExacta && !summary.errorAbsoluto) {
    return null;
  }
  return summary;
}

function renderLagrangeSummary(summary) {
  const expresionContenido = summary.expresionFinalLatex
    ? `<div class=\"lagrange-latex\">\\(${escapeHtml(summary.expresionFinalLatex)}\\)</div>`
    : `<p>${escapeHtml(summary.expresionFinal || "N/A")}</p>`;

  outputTable.classList.remove("output-empty");
  outputTable.innerHTML = `
    <section class=\"lagrange-summary\">
      <article class=\"lagrange-card\">
        <h3>Expresión Final</h3>
        ${expresionContenido}
      </article>
      <article class=\"lagrange-card\">
        <h3>Error Local</h3>
        <p>${escapeHtml(summary.errorLocal || "N/A")}</p>
      </article>
      <article class=\"lagrange-card\">
        <h3>Error Global</h3>
        <p>${escapeHtml(summary.errorGlobal || "N/A")}</p>
      </article>
    </section>
  `;

  if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
    window.MathJax.typesetPromise([outputTable]).catch(() => {});
  }
}

function renderDiferenciaFinitaSummary(summary) {
  const cards = [
    `
      <article class="lagrange-card">
        <h3>Derivada Aproximada</h3>
        <p>${escapeHtml(summary.derivada || "N/A")}</p>
      </article>
    `,
  ];

  const exactValue = String(summary.derivadaExacta || "").trim();
  if (exactValue && exactValue.toUpperCase() !== "N/A") {
    cards.push(
      `
        <article class="lagrange-card">
          <h3>Derivada Exacta</h3>
          <p>${escapeHtml(summary.derivadaExacta)}</p>
        </article>
      `
    );
  }

  const errorValue = String(summary.errorAbsoluto || "").trim();
  if (errorValue && errorValue.toUpperCase() !== "N/A") {
    cards.push(
      `
        <article class="lagrange-card">
          <h3>Error Absoluto</h3>
          <p>${escapeHtml(summary.errorAbsoluto)}</p>
        </article>
      `
    );
  }

  outputTable.classList.remove("output-empty");
  outputTable.innerHTML = `
    <section class="lagrange-summary">
      ${cards.join("")}
    </section>
  `;
}

function renderOutput(rawText, methodKey = null) {
  const text = rawText || "Sin salida";

  if (methodKey === "lagrange") {
    const lagrangeSummary = parseLagrangeSummary(text);
    if (lagrangeSummary) {
      renderLagrangeSummary(lagrangeSummary);
      return;
    }
  }

  if (methodKey === "diferencia_finita") {
    const diferenciaSummary = parseDiferenciaFinitaSummary(text);
    if (diferenciaSummary) {
      renderDiferenciaFinitaSummary(diferenciaSummary);
      return;
    }
  }

  const parsed = parseTabulateGrid(text);
  if (!parsed) {
    outputTable.classList.add("output-empty");
    outputTable.textContent = text;
    return;
  }
  renderTable(parsed);
}

function createInput(field) {
  const wrapper = document.createElement("div");
  wrapper.className = "field";
  wrapper.dataset.fieldKey = field.key;

  const label = document.createElement("label");
  label.htmlFor = field.key;
  label.textContent = field.label;
  wrapper.appendChild(label);

  let input;
  if (Array.isArray(field.options) && field.options.length > 0) {
    input = document.createElement("select");
    input.id = field.key;
    for (const opt of field.options) {
      const option = document.createElement("option");
      option.value = opt;
      option.textContent = opt;
      if (String(field.default) === opt) {
        option.selected = true;
      }
      input.appendChild(option);
    }
  } else {
    input = document.createElement("input");
    input.id = field.key;
    input.type = "text";
    if (field.kind === "float") {
      input.inputMode = "decimal";
    }
    input.value = String(field.default ?? "");
  }

  const irrationalButtons = buildIrrationalButtons(field, input);
  if (irrationalButtons) {
    wrapper.appendChild(irrationalButtons);
  }
  wrapper.appendChild(input);
  return wrapper;
}

function insertSpecialConstant(input, token, useListSeparator = false) {
  if (!useListSeparator) {
    insertIntoInput(input, token);
    return;
  }

  const value = input.value || "";
  const start = input.selectionStart ?? value.length;
  const needsSeparator = start > 0 && /[^\s,]$/.test(value.slice(0, start));
  const prefix = needsSeparator ? ", " : "";
  insertIntoInput(input, `${prefix}${token}`);
}

function buildIrrationalButtons(field, input) {
  const isLagrangeListField = ["x_nodos", "y_nodos"].includes(field.key);
  const supportsIrrationalButtons = field.kind === "float" || ["x_eval"].includes(field.key);
  if (!supportsIrrationalButtons) {
    return null;
  }

  const toolbar = document.createElement("div");
  toolbar.className = "irrational-ops";

  const constants = [
    { label: "π", token: "π", title: "Insertar pi" },
    { label: "e", token: "euler", title: "Insertar euler" },
  ];

  for (const item of constants) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "irrational-op-btn";
    button.textContent = item.label;
    button.title = item.title;
    button.addEventListener("click", () => {
      insertSpecialConstant(input, item.token, isLagrangeListField);
    });
    toolbar.appendChild(button);
  }

  return toolbar;
}

function insertIntoInput(input, text, cursorOffset = 0) {
  const start = input.selectionStart ?? input.value.length;
  const end = input.selectionEnd ?? input.value.length;
  input.value = `${input.value.slice(0, start)}${text}${input.value.slice(end)}`;
  const nextPos = start + text.length + cursorOffset;
  input.setSelectionRange(nextPos, nextPos);
  input.focus();
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

function buildExpressionToolbar(expressionInput) {
  const toolbar = document.createElement("div");
  toolbar.className = "expr-ops";

  for (const op of EXPRESSION_OPS) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "expr-op-btn";
    button.textContent = op.label;
    button.addEventListener("click", () => {
      insertIntoInput(expressionInput, op.insert, op.cursorOffset || 0);
    });
    toolbar.appendChild(button);
  }

  return toolbar;
}

function placeLatexPreviewUnderExpressionField() {
  const expressionWrapper = methodForm.querySelector('[data-field-key="f_expr"], [data-field-key="g_expr"]');
  if (!expressionWrapper) {
    clearLatexPreview();
    return;
  }

  const expressionInput = expressionWrapper.querySelector("input");
  if (expressionInput) {
    expressionWrapper.insertBefore(buildExpressionToolbar(expressionInput), expressionInput);
  }
  expressionWrapper.appendChild(latexPreviewBox);
}

function applyLagrangeMode(mode) {
  const exprWrapper = methodForm.querySelector('[data-field-key="f_expr"]');
  const imagesWrapper = methodForm.querySelector('[data-field-key="y_nodos"]');
  const xEvalWrapper = methodForm.querySelector('[data-field-key="x_eval"]');
  const exprInput = document.getElementById("f_expr");
  const imagesInput = document.getElementById("y_nodos");
  const xEvalInput = document.getElementById("x_eval");
  const usingNodeEditor = Boolean(methodForm.querySelector(".lagrange-node-editor"));

  if (!exprWrapper || !imagesWrapper || !exprInput || !imagesInput || !xEvalWrapper || !xEvalInput) {
    return;
  }

  const usingImages = mode === "images";

  exprWrapper.style.display = usingImages ? "none" : "grid";
  imagesWrapper.style.display = usingNodeEditor ? "none" : (usingImages ? "grid" : "none");
  xEvalWrapper.style.display = usingImages ? "none" : "grid";

  exprInput.disabled = usingImages;
  imagesInput.disabled = !usingImages;
  xEvalInput.disabled = usingImages;

  methodForm.dataset.lagrangeMode = usingImages ? "images" : "expr";

  applyPersistedLagrangeInputsForMode(methodForm.dataset.lagrangeMode);

  const tabs = methodForm.querySelectorAll(".lagrange-tab");
  tabs.forEach((tab) => {
    const isActive = tab.dataset.mode === methodForm.dataset.lagrangeMode;
    tab.classList.toggle("active", isActive);
    tab.setAttribute("aria-selected", isActive ? "true" : "false");
  });

  if (usingImages) {
    clearLatexPreview();
  } else {
    scheduleLatexPreview();
  }

  refreshLagrangeNodeEditorMode();
}

function addLagrangeTabs() {
  const exprWrapper = methodForm.querySelector('[data-field-key="f_expr"]');
  const imagesWrapper = methodForm.querySelector('[data-field-key="y_nodos"]');
  if (!exprWrapper || !imagesWrapper) {
    return;
  }

  const tabs = document.createElement("div");
  tabs.className = "lagrange-tabs";

  const exprBtn = document.createElement("button");
  exprBtn.type = "button";
  exprBtn.className = "lagrange-tab";
  exprBtn.dataset.mode = "expr";
  exprBtn.textContent = "Con expresión";
  exprBtn.addEventListener("click", () => {
    applyLagrangeMode("expr");
    persistMethodInputs("lagrange");
  });

  const imagesBtn = document.createElement("button");
  imagesBtn.type = "button";
  imagesBtn.className = "lagrange-tab";
  imagesBtn.dataset.mode = "images";
  imagesBtn.textContent = "Con imágenes";
  imagesBtn.addEventListener("click", () => {
    applyLagrangeMode("images");
    persistMethodInputs("lagrange");
  });

  tabs.appendChild(exprBtn);
  tabs.appendChild(imagesBtn);
  methodForm.insertBefore(tabs, exprWrapper);

  applyLagrangeMode(getPersistedLagrangeMode());
}

function parseNodeList(text) {
  return String(text || "")
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function buildLagrangeNodeRow(xValue = "", yValue = "") {
  const row = document.createElement("div");
  row.className = "lagrange-node-row";

  const xField = document.createElement("div");
  xField.className = "lagrange-node-field lagrange-node-field-x";

  const xInput = document.createElement("input");
  xInput.type = "text";
  xInput.className = "lagrange-node-x";
  xInput.placeholder = "x_i";
  xInput.value = xValue;

  const xButtons = buildIrrationalButtons({ key: "x_eval", kind: "float" }, xInput);
  if (xButtons) {
    xField.appendChild(xButtons);
  }
  xField.appendChild(xInput);

  const yField = document.createElement("div");
  yField.className = "lagrange-node-field lagrange-node-field-y";

  const yInput = document.createElement("input");
  yInput.type = "text";
  yInput.className = "lagrange-node-y";
  yInput.placeholder = "y_i";
  yInput.value = yValue;

  const yButtons = buildIrrationalButtons({ key: "x_eval", kind: "float" }, yInput);
  if (yButtons) {
    yField.appendChild(yButtons);
  }
  yField.appendChild(yInput);

  const removeBtn = document.createElement("button");
  removeBtn.type = "button";
  removeBtn.className = "lagrange-node-remove";
  removeBtn.textContent = "-";
  removeBtn.title = "Eliminar nodo";

  row.appendChild(xField);
  row.appendChild(yField);
  row.appendChild(removeBtn);
  return row;
}

function syncHiddenInputsToLagrangeNodeEditor() {
  const editor = methodForm.querySelector(".lagrange-node-editor");
  const xInputHidden = document.getElementById("x_nodos");
  const yInputHidden = document.getElementById("y_nodos");
  if (!editor || !xInputHidden || !yInputHidden) {
    return;
  }

  const rowsContainer = editor.querySelector(".lagrange-node-rows");
  if (!rowsContainer) {
    return;
  }

  const xs = parseNodeList(xInputHidden.value);
  const ys = parseNodeList(yInputHidden.value);
  const rowCount = Math.max(xs.length, ys.length, 1);

  rowsContainer.innerHTML = "";
  for (let i = 0; i < rowCount; i += 1) {
    rowsContainer.appendChild(buildLagrangeNodeRow(xs[i] || "", ys[i] || ""));
  }
}

function syncLagrangeNodeEditorToHidden() {
  const editor = methodForm.querySelector(".lagrange-node-editor");
  const xInputHidden = document.getElementById("x_nodos");
  const yInputHidden = document.getElementById("y_nodos");
  if (!editor || !xInputHidden || !yInputHidden) {
    return;
  }

  const rows = Array.from(editor.querySelectorAll(".lagrange-node-row"));

  const xs = [];
  const ys = [];
  for (const row of rows) {
    const xVal = (row.querySelector(".lagrange-node-x")?.value || "").trim();
    const yVal = (row.querySelector(".lagrange-node-y")?.value || "").trim();

    if (xVal) {
      xs.push(xVal);
      if (yVal) {
        ys.push(yVal);
      }
    }
  }

  xInputHidden.value = xs.join(", ");
  yInputHidden.value = ys.join(", ");
}

function refreshLagrangeNodeEditorMode() {
  const editor = methodForm.querySelector(".lagrange-node-editor");
  if (!editor) {
    return;
  }

  const usingImages = methodForm.dataset.lagrangeMode === "images";
  editor.classList.toggle("images-mode", usingImages);
  syncLagrangeNodeEditorToHidden();
}

function setupLagrangeNodeEditor() {
  const xWrapper = methodForm.querySelector('[data-field-key="x_nodos"]');
  const yWrapper = methodForm.querySelector('[data-field-key="y_nodos"]');
  const xInputHidden = document.getElementById("x_nodos");
  const yInputHidden = document.getElementById("y_nodos");

  if (!xWrapper || !yWrapper || !xInputHidden || !yInputHidden) {
    return;
  }

  xInputHidden.style.display = "none";
  yInputHidden.style.display = "none";
  yWrapper.style.display = "none";

  if (xWrapper.querySelector(".lagrange-node-editor")) {
    refreshLagrangeNodeEditorMode();
    return;
  }

  const editor = document.createElement("div");
  editor.className = "lagrange-node-editor";

  const controls = document.createElement("div");
  controls.className = "lagrange-node-controls";
  const addBtn = document.createElement("button");
  addBtn.type = "button";
  addBtn.className = "lagrange-node-add";
  addBtn.textContent = "+ Agregar nodo";
  controls.appendChild(addBtn);

  const rowsContainer = document.createElement("div");
  rowsContainer.className = "lagrange-node-rows";

  const xs = parseNodeList(xInputHidden.value);
  const ys = parseNodeList(yInputHidden.value);
  const rowCount = Math.max(xs.length, ys.length, 1);

  for (let i = 0; i < rowCount; i += 1) {
    rowsContainer.appendChild(buildLagrangeNodeRow(xs[i] || "", ys[i] || ""));
  }

  editor.appendChild(controls);
  editor.appendChild(rowsContainer);
  xWrapper.appendChild(editor);

  addBtn.addEventListener("click", () => {
    rowsContainer.appendChild(buildLagrangeNodeRow());
    refreshLagrangeNodeEditorMode();
    persistMethodInputs("lagrange");
  });

  rowsContainer.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement) || !target.classList.contains("lagrange-node-remove")) {
      return;
    }

    const rows = rowsContainer.querySelectorAll(".lagrange-node-row");
    if (rows.length <= 1) {
      return;
    }

    const row = target.closest(".lagrange-node-row");
    if (row) {
      row.remove();
      refreshLagrangeNodeEditorMode();
      persistMethodInputs("lagrange");
    }
  });

  rowsContainer.addEventListener("input", () => {
    refreshLagrangeNodeEditorMode();
    persistMethodInputs("lagrange");
  });

  refreshLagrangeNodeEditorMode();
}

function applyDiferenciaFinitaMode(mode) {
  const exprWrapper = methodForm.querySelector('[data-field-key="f_expr"]');
  const xWrapper = methodForm.querySelector('[data-field-key="x"]');
  const yXm1Wrapper = methodForm.querySelector('[data-field-key="y_xm1"]');
  const yXWrapper = methodForm.querySelector('[data-field-key="y_x"]');
  const yXp1Wrapper = methodForm.querySelector('[data-field-key="y_xp1"]');

  const exprInput = document.getElementById("f_expr");
  const xInput = document.getElementById("x");
  const yXm1Input = document.getElementById("y_xm1");
  const yXInput = document.getElementById("y_x");
  const yXp1Input = document.getElementById("y_xp1");

  if (!exprWrapper || !xWrapper || !exprInput || !xInput || !yXm1Wrapper || !yXWrapper || !yXp1Wrapper) {
    return;
  }

  const usingImages = mode === "images";

  exprWrapper.style.display = usingImages ? "none" : "grid";
  xWrapper.style.display = usingImages ? "none" : "grid";

  exprInput.disabled = usingImages;
  xInput.disabled = usingImages;

  methodForm.dataset.diferenciaFinitaMode = usingImages ? "images" : "expr";
  applyPersistedDiferenciaFinitaInputsForMode(methodForm.dataset.diferenciaFinitaMode);

  const metodoValue = (document.getElementById("metodo")?.value || "").trim().toLowerCase();
  const metodoKey = metodoValue
    .replaceAll("á", "a")
    .replaceAll("é", "e")
    .replaceAll("í", "i")
    .replaceAll("ó", "o")
    .replaceAll("ú", "u");

  const isProgresivo = metodoKey === "progresivo" || metodoKey === "adelante";
  const isRegresivo = metodoKey === "regresivo" || metodoKey === "atras";
  const isCentral = metodoKey === "central" || metodoKey === "centrada";

  const showYm1 = usingImages && (isRegresivo || isCentral);
  const showY = usingImages && (isProgresivo || isRegresivo);
  const showYp1 = usingImages && (isProgresivo || isCentral);

  yXm1Wrapper.style.display = showYm1 ? "grid" : "none";
  yXWrapper.style.display = showY ? "grid" : "none";
  yXp1Wrapper.style.display = showYp1 ? "grid" : "none";

  if (yXm1Input) {
    yXm1Input.disabled = !showYm1;
  }
  if (yXInput) {
    yXInput.disabled = !showY;
  }
  if (yXp1Input) {
    yXp1Input.disabled = !showYp1;
  }

  const tabs = methodForm.querySelectorAll(".diferencia-finita-tab");
  tabs.forEach((tab) => {
    const isActive = tab.dataset.mode === methodForm.dataset.diferenciaFinitaMode;
    tab.classList.toggle("active", isActive);
    tab.setAttribute("aria-selected", isActive ? "true" : "false");
  });

  if (usingImages) {
    clearLatexPreview();
  } else {
    scheduleLatexPreview();
  }

  const currentMethod = selectedMethod();
  const canPlot = shouldRenderPlot(currentMethod);
  if (chartPanel) {
    chartPanel.style.display = canPlot ? "block" : "none";
  }
  if (!canPlot) {
    clearPlot();
    setPlotMessage("En 'Con imágenes' no se grafica porque no hay una función explícita f(x).");
  } else {
    setPlotMessage("Ejecutá el método para generar el gráfico.");
  }
}

function addDiferenciaFinitaTabs() {
  const exprWrapper = methodForm.querySelector('[data-field-key="f_expr"]');
  if (!exprWrapper) {
    return;
  }

  const tabs = document.createElement("div");
  tabs.className = "lagrange-tabs";

  const exprBtn = document.createElement("button");
  exprBtn.type = "button";
  exprBtn.className = "lagrange-tab diferencia-finita-tab";
  exprBtn.dataset.mode = "expr";
  exprBtn.textContent = "Con expresión";
  exprBtn.addEventListener("click", () => {
    applyDiferenciaFinitaMode("expr");
    persistMethodInputs("diferencia_finita");
  });

  const imagesBtn = document.createElement("button");
  imagesBtn.type = "button";
  imagesBtn.className = "lagrange-tab diferencia-finita-tab";
  imagesBtn.dataset.mode = "images";
  imagesBtn.textContent = "Con imágenes";
  imagesBtn.addEventListener("click", () => {
    applyDiferenciaFinitaMode("images");
    persistMethodInputs("diferencia_finita");
  });

  tabs.appendChild(exprBtn);
  tabs.appendChild(imagesBtn);
  methodForm.insertBefore(tabs, exprWrapper);

  const metodoInput = document.getElementById("metodo");
  if (metodoInput) {
    metodoInput.addEventListener("change", () => {
      applyDiferenciaFinitaMode(methodForm.dataset.diferenciaFinitaMode || "expr");
      persistMethodInputs("diferencia_finita");
    });
  }

  applyDiferenciaFinitaMode(getPersistedDiferenciaFinitaMode());
}

function collectParams(method) {
  if (isDiferenciaFinitaMethod(method)) {
    const mode = methodForm.dataset.diferenciaFinitaMode === "images" ? "images" : "expr";
    const xValue = (document.getElementById("x")?.value || "").trim();
    const hValue = (document.getElementById("h")?.value || "").trim();
    const metodoValue = (document.getElementById("metodo")?.value || "").trim();
    const fExprValue = (document.getElementById("f_expr")?.value || "").trim();
    const yXm1Value = (document.getElementById("y_xm1")?.value || "").trim();
    const yXValue = (document.getElementById("y_x")?.value || "").trim();
    const yXp1Value = (document.getElementById("y_xp1")?.value || "").trim();

    if (!hValue) {
      throw new Error("Completá el campo 'Paso h'.");
    }
    if (!metodoValue) {
      throw new Error("Seleccioná un esquema de diferencia finita.");
    }

    if (mode === "expr") {
      if (!xValue) {
        throw new Error("Completá el campo 'Punto de evaluación x' en la pestaña 'Con expresión'.");
      }
      if (!fExprValue) {
        throw new Error("Completá 'Función f(x)' en la pestaña 'Con expresión'.");
      }

      return {
        f_expr: fExprValue,
        x: xValue,
        h: hValue,
        metodo: metodoValue,
        y_xm1: "",
        y_x: "",
        y_xp1: "",
      };
    }

    const metodoKey = metodoValue
      .toLowerCase()
      .replaceAll("á", "a")
      .replaceAll("é", "e")
      .replaceAll("í", "i")
      .replaceAll("ó", "o")
      .replaceAll("ú", "u");
    if (metodoKey === "progresivo" || metodoKey === "adelante") {
      if (!yXValue || !yXp1Value) {
        throw new Error("Para 'Progresivo', completá f(x) y f(x+h). ");
      }
    } else if (metodoKey === "regresivo" || metodoKey === "atras") {
      if (!yXm1Value || !yXValue) {
        throw new Error("Para 'Regresivo', completá f(x-h) y f(x). ");
      }
    } else if (metodoKey === "central" || metodoKey === "centrada") {
      if (!yXm1Value || !yXp1Value) {
        throw new Error("Para 'Central', completá f(x-h) y f(x+h). ");
      }
    } else {
      throw new Error("El esquema seleccionado no es válido.");
    }

    return {
      f_expr: "",
      x: "",
      h: hValue,
      metodo: metodoValue,
      y_xm1: yXm1Value,
      y_x: yXValue,
      y_xp1: yXp1Value,
    };
  }

  if (isLagrangeMethod(method)) {
    const mode = methodForm.dataset.lagrangeMode === "images" ? "images" : "expr";
    const xNodosValue = (document.getElementById("x_nodos")?.value || "").trim();
    const xEvalValue = (document.getElementById("x_eval")?.value || "").trim();
    const fExprValue = (document.getElementById("f_expr")?.value || "").trim();
    const yNodosValue = (document.getElementById("y_nodos")?.value || "").trim();

    if (!xNodosValue) {
      throw new Error("Completá el campo 'Nodos x (separados por coma)'.");
    }

    if (mode === "expr") {
      if (!xEvalValue) {
        throw new Error("Completá 'Punto de evaluación' en la pestaña 'Con expresión'.");
      }
      if (!fExprValue) {
        throw new Error("Completá 'Función f(x)' en la pestaña 'Con expresión'.");
      }
      return {
        f_expr: fExprValue,
        x_nodos: xNodosValue,
        y_nodos: "",
        x_eval: xEvalValue,
      };
    }

    if (!yNodosValue) {
      throw new Error("Completá 'Imágenes y (separadas por coma)' en la pestaña 'Con imágenes'.");
    }

    return {
      f_expr: "",
      x_nodos: xNodosValue,
      y_nodos: yNodosValue,
      x_eval: "",
    };
  }

  const params = {};
  for (const field of method.fields) {
    const element = document.getElementById(field.key);
    const value = element.value?.trim();
    const isOptional = Boolean(field.optional);
    if (!value && !isOptional) {
      throw new Error(`Completá el campo '${field.label}'.`);
    }
    if (!value && isOptional) {
      params[field.key] = "";
      continue;
    }
    params[field.key] = value;
  }
  return params;
}

function parseGlobalNumber(input, label, { integer = false } = {}) {
  const raw = input.value.trim();
  if (raw === "") {
    return null;
  }

  const value = Number(raw);
  if (Number.isNaN(value)) {
    throw new Error(`El parámetro global '${label}' debe ser numérico.`);
  }
  if (integer && !Number.isInteger(value)) {
    throw new Error(`El parámetro global '${label}' debe ser entero.`);
  }
  return value;
}

function collectGlobalConfig() {
  const iteraciones = parseGlobalNumber(globalIteracionesInput, "Iteraciones", { integer: true });
  const toleranciaExp = parseGlobalNumber(globalToleranciaInput, "Tolerancia (x)", { integer: true });
  const precision = parseGlobalNumber(globalPrecisionInput, "Precision", { integer: true });
  const porcentaje = parseGlobalNumber(globalPorcentajeInput, "Porcentaje");

  if (iteraciones !== null && iteraciones <= 0) {
    throw new Error("Iteraciones debe ser > 0.");
  }
  if (toleranciaExp !== null && toleranciaExp < 0) {
    throw new Error("El exponente x de tolerancia debe ser >= 0.");
  }
  if (precision !== null && precision < 0) {
    throw new Error("Precision debe ser >= 0.");
  }
  if (porcentaje !== null && porcentaje <= 0) {
    throw new Error("Porcentaje debe ser > 0.");
  }

  const tolerancia = toleranciaExp === null ? null : 10 ** (-toleranciaExp);

  return {
    iteraciones,
    tolerancia,
    toleranciaExp,
    precision,
    porcentaje,
    debugMode: globalDebugModeInput.checked,
  };
}

function percentile(sortedValues, p) {
  if (!sortedValues.length) {
    return 0;
  }
  if (sortedValues.length === 1) {
    return sortedValues[0];
  }
  const index = (sortedValues.length - 1) * p;
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  const weight = index - lower;
  return sortedValues[lower] * (1 - weight) + sortedValues[upper] * weight;
}

function buildPlotSeries(points) {
  if (!points.length) {
    return { x: [], y: [] };
  }

  const xs = points.map((p) => p[0]);
  const ys = points.map((p) => p[1]);
  const ySorted = [...ys].sort((a, b) => a - b);

  const q10 = percentile(ySorted, 0.1);
  const q90 = percentile(ySorted, 0.9);
  const ySpan = Math.max(q90 - q10, 1);

  const dxs = [];
  for (let i = 1; i < points.length; i += 1) {
    dxs.push(points[i][0] - points[i - 1][0]);
  }
  const dxSorted = dxs.sort((a, b) => a - b);
  const medianDx = percentile(dxSorted, 0.5) || 0;
  const jumpThreshold = Math.max(ySpan * 1.1, 2);

  const px = [];
  const py = [];

  for (let i = 0; i < points.length; i += 1) {
    if (i > 0) {
      const prev = points[i - 1];
      const current = points[i];
      const dy = Math.abs(current[1] - prev[1]);
      const dx = current[0] - prev[0];
      const brokenByJump = dy > jumpThreshold;
      const brokenByGap = medianDx > 0 && dx > medianDx * 1.8;
      if (brokenByJump || brokenByGap) {
        px.push(null);
        py.push(null);
      }
    }

    px.push(points[i][0]);
    py.push(points[i][1]);
  }

  return { x: px, y: py, rawX: xs, rawY: ys };
}

function computeSymmetricRange(plotTraces, fallback = 6) {
  let maxAbs = 0;
  for (const trace of plotTraces) {
    for (const x of trace.x || []) {
      if (typeof x === "number" && Number.isFinite(x)) {
        maxAbs = Math.max(maxAbs, Math.abs(x));
      }
    }
    for (const y of trace.y || []) {
      if (typeof y === "number" && Number.isFinite(y)) {
        maxAbs = Math.max(maxAbs, Math.abs(y));
      }
    }
  }

  if (!Number.isFinite(maxAbs) || maxAbs <= 0) {
    return [-fallback, fallback];
  }

  const radius = Math.min(10, Math.max(4, Math.ceil(maxAbs * 1.1)));
  return [-radius, radius];
}

function applyInitialZoom(range, zoomSteps = 2) {
  const min = Number(range?.[0]);
  const max = Number(range?.[1]);
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    return [-5, 5];
  }

  const currentRadius = Math.max(Math.abs(min), Math.abs(max));
  const _ = zoomSteps;
  const initialRadius = 5;
  const clampedRadius = Math.max(2.0, Math.min(currentRadius, initialRadius));
  return [-clampedRadius, clampedRadius];
}

function toPlotlyTrace(traceDef, index) {
  const points = Array.isArray(traceDef?.points) ? traceDef.points : [];
  const kind = traceDef?.kind === "markers" ? "markers" : "line";
  const name = String(traceDef?.name || `Serie ${index + 1}`);
  const dash = typeof traceDef?.dash === "string" ? traceDef.dash : "solid";

  if (kind === "markers") {
    return {
      type: "scatter",
      mode: "markers",
      name,
      x: points.map((p) => p[0]),
      y: points.map((p) => p[1]),
      marker: {
        size: 9,
        color: "#d1495b",
        line: { color: "#ffffff", width: 1.2 },
      },
      hovertemplate: `${name}<br>x=%{x:.6g}<br>y=%{y:.6g}<extra></extra>`,
    };
  }

  const series = buildPlotSeries(points);
  const palette = ["#0f8b8d", "#2f6fed", "#ef6c00", "#6a1b9a"];
  return {
    type: "scatter",
    mode: "lines",
    name,
    x: series.x,
    y: series.y,
    line: {
      color: palette[index % palette.length],
      width: 2.4,
      dash,
    },
    connectgaps: false,
    hoverdistance: 24,
    hovertemplate: `${name}<br>x=%{x:.6g}<br>y=%{y:.6g}<extra></extra>`,
  };
}

async function renderPlot(traceDefs) {
  if (!window.Plotly) {
    setPlotMessage("Plotly no esta disponible.");
    return;
  }

  const plotTraces = (traceDefs || []).map((trace, i) => toPlotlyTrace(trace, i));
  const [baseMin, baseMax] = computeSymmetricRange(plotTraces);
  const [yMinRange, yMaxRange] = applyInitialZoom([baseMin, baseMax], 0);

  const yRadius = Math.max(Math.abs(yMinRange), Math.abs(yMaxRange));
  const containerWidth = Math.max(1, Number(plotlyChart?.clientWidth) || 1);
  const containerHeight = Math.max(1, Number(plotlyChart?.clientHeight) || 1);
  const aspectRatio = containerWidth / containerHeight;

  // Fill horizontal space by extending x while preserving square grid cells.
  const suggestedXRadius = yRadius * aspectRatio;
  const xRadius = Math.min(10, Math.max(yRadius, suggestedXRadius));
  const xMinRange = -xRadius;
  const xMaxRange = xRadius;

  const layout = {
    margin: { l: 58, r: 24, t: 34, b: 48 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "#ffffff",
    showlegend: true,
    legend: {
      orientation: "h",
      y: 1.08,
      x: 0,
      bgcolor: "rgba(255,255,255,0.92)",
      bordercolor: "#d4e4ea",
      borderwidth: 1,
    },
    dragmode: "pan",
    hovermode: "closest",
    xaxis: {
      title: "x",
      showgrid: true,
      gridcolor: "#dfe7ec",
      gridwidth: 1,
      zeroline: true,
      zerolinecolor: "#111827",
      zerolinewidth: 2,
      autorange: false,
      range: [xMinRange, xMaxRange],
      dtick: 1,
      automargin: true,
      scaleanchor: "y",
      scaleratio: 1,
      constrain: "domain",
    },
    yaxis: {
      title: "y",
      showgrid: true,
      gridcolor: "#dfe7ec",
      gridwidth: 1,
      zeroline: true,
      zerolinecolor: "#111827",
      zerolinewidth: 2,
      autorange: false,
      range: [yMinRange, yMaxRange],
      dtick: 1,
      automargin: true,
      constrain: "domain",
    },
    annotations: [],
  };

  const config = {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["select2d", "lasso2d", "autoScale2d", "toImage"],
    scrollZoom: true,
  };

  await window.Plotly.react(plotlyChart, plotTraces, layout, config);

  setPlotMessage("");
}

async function requestPlot(methodOverride = null, paramsOverride = null) {
  const method = methodOverride || selectedMethod();
  if (!method) {
    return;
  }

  let params = paramsOverride;
  if (!params) {
    try {
      params = collectParams(method);
    } catch (error) {
      clearPlot();
      setPlotMessage(`No se pudo graficar: ${String(error.message || error)}`);
      return;
    }
  }

  setPlotMessage("Generando gráfico...");

  let globalConfig;
  try {
    globalConfig = collectGlobalConfig();
  } catch (error) {
    clearPlot();
    setPlotMessage(String(error.message || error));
    return;
  }

  try {
    const response = await fetch("/api/plot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ method: method.key, params, global_config: globalConfig }),
    });

    const data = await response.json();
    if (!response.ok || !data.success) {
      clearPlot();
      setPlotMessage(data.error || "No se pudo graficar la función.");
      return;
    }

    const traceDefs = Array.isArray(data.traces)
      ? data.traces
      : (Array.isArray(data.points) ? [{ name: "Función", kind: "line", points: data.points }] : []);

    await renderPlot(traceDefs);
  } catch (error) {
    clearPlot();
    setPlotMessage(`Error de conexión al graficar: ${String(error)}`);
  }
}

function renderForm() {
  const method = selectedMethod();
  if (!method) {
    methodDescription.textContent = "";
    methodForm.innerHTML = "";
    clearPlot();
    clearLatexPreview();
    setPlotMessage("Elegí un método para ver su gráfico.");
    updateFixedPointHelpVisibility(null);
    return;
  }

  methodDescription.textContent = method.description;
  methodForm.innerHTML = "";

  for (const field of method.fields) {
    methodForm.appendChild(createInput(field));
  }

  placeLatexPreviewUnderExpressionField();
  applyPersistedMethodInputs(method.key);

  if (isLagrangeMethod(method)) {
    addLagrangeTabs();
    setupLagrangeNodeEditor();
  }

  if (isDiferenciaFinitaMethod(method)) {
    addDiferenciaFinitaTabs();
  }

  clearPlot();
  setPlotMessage(shouldRenderPlot(method) ? "Ejecutá el método para generar el gráfico." : "Este método no tiene visualización gráfica.");
  if (chartPanel) {
    chartPanel.style.display = shouldRenderPlot(method) ? "block" : "none";
  }
  updateFixedPointHelpVisibility(method);
  scheduleLatexPreview();
}

async function runMethod() {
  const method = selectedMethod();
  if (!method) {
    return;
  }

  const runId = ++activeRunId;

  let params;
  let globalConfig;
  try {
    params = collectParams(method);
    globalConfig = collectGlobalConfig();
  } catch (error) {
    setStatus("error", "Entrada inválida");
    renderOutput(String(error.message || error), method.key);
    return;
  }

  setStatus("idle", "Ejecutando...");
  renderOutput("Procesando resultados...");

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ method: method.key, params, global_config: globalConfig }),
    });

    const data = await response.json();
    if (runId !== activeRunId || methodSelect.value !== method.key) {
      return;
    }
    if (!response.ok || !data.success) {
      setStatus("error", "Error");
      renderOutput(data.error || "Error al ejecutar el método.", method.key);
      return;
    }

    setStatus("ok", "Correcto");
    renderOutput(data.output || "Sin salida", method.key);
    if (shouldRenderPlot(method, params)) {
      await requestPlot(method, params);
    } else {
      clearPlot();
      setPlotMessage("En 'Con imágenes' no se grafica porque no hay una función explícita f(x).");
    }
  } catch (error) {
    if (runId !== activeRunId || methodSelect.value !== method.key) {
      return;
    }
    setStatus("error", "Conexión");
    renderOutput(`No se pudo conectar con el servidor: ${String(error)}`, method.key);
  }
}

async function bootstrap() {
  loadPersistedState();
  applyPersistedGlobalInputs();

  setStatus("idle", "Cargando...");
  const response = await fetch("/api/methods");
  methods = await response.json();

  methodSelect.innerHTML = "";
  for (const method of methods) {
    const option = document.createElement("option");
    option.value = method.key;
    option.textContent = method.label;
    methodSelect.appendChild(option);
  }

  if (persistedState.selectedMethod) {
    const exists = methods.some((method) => method.key === persistedState.selectedMethod);
    if (exists) {
      methodSelect.value = persistedState.selectedMethod;
    }
  }

  renderForm();
  setStatus("idle", "Listo");
}

methodSelect.addEventListener("change", () => {
  activeRunId += 1;
  persistedState.selectedMethod = methodSelect.value;
  savePersistedState();
  clearOutput();
  clearPlot();
  setPlotMessage("Ejecutá el método para generar el gráfico.");
  setStatus("idle", "Listo");
  renderForm();
});

methodForm.addEventListener("input", () => {
  const method = selectedMethod();
  if (!method) {
    return;
  }
  persistMethodInputs(method.key);
  scheduleLatexPreview();
});

for (const input of [
  globalIteracionesInput,
  globalToleranciaInput,
  globalPrecisionInput,
  globalPorcentajeInput,
  globalDebugModeInput,
]) {
  input.addEventListener("input", persistGlobalInputs);
}

runButton.addEventListener("click", runMethod);

if (fixedPointHelpButton) {
  fixedPointHelpButton.addEventListener("click", openFixedPointHelpModal);
}
if (fixedPointHelpClose) {
  fixedPointHelpClose.addEventListener("click", closeFixedPointHelpModal);
}
if (fixedPointHelpBackdrop) {
  fixedPointHelpBackdrop.addEventListener("click", closeFixedPointHelpModal);
}
if (fixedPointHelpSuggest) {
  fixedPointHelpSuggest.addEventListener("click", suggestFixedPointFunction);
}
if (fixedPointHelpInput) {
  fixedPointHelpInput.addEventListener("input", scheduleFixedPointHelpPreview);
}
if (fixedPointHelpResult) {
  fixedPointHelpResult.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }
    if (!target.classList.contains("fixed-help-copy-icon")) {
      return;
    }
    copySuggestedGToMethodField();
  });
}

bootstrap().catch((error) => {
  setStatus("error", "Carga fallida");
  renderOutput(`No se pudieron cargar los métodos: ${String(error)}`);
  clearPlot();
  setPlotMessage(`No se pudo inicializar el gráfico: ${String(error)}`);
});
