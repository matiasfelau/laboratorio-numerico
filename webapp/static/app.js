const methodSelect = document.getElementById("methodSelect");
const methodDescription = document.getElementById("methodDescription");
const methodForm = document.getElementById("methodForm");
const runButton = document.getElementById("runButton");
const outputTable = document.getElementById("outputTable");
const statusBadge = document.getElementById("statusBadge");
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

let methods = [];
let latexPreviewTimer = null;

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
  { label: "pi", insert: "pi" },
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

function setPlotMessage(message) {
  plotMessage.textContent = message;
}

function clearPlot() {
  if (window.Plotly && plotlyChart) {
    window.Plotly.purge(plotlyChart);
  }
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

  persistedState.paramsByMethod[methodKey] = values;
  savePersistedState();
}

function applyPersistedMethodInputs(methodKey) {
  const methodValues = persistedState.paramsByMethod?.[methodKey];
  if (!methodValues) {
    return;
  }
  for (const [fieldKey, value] of Object.entries(methodValues)) {
    const element = document.getElementById(fieldKey);
    if (element) {
      element.value = String(value ?? "");
    }
  }
}

function getExpressionInput() {
  return document.getElementById("f_expr") || document.getElementById("g_expr");
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

function renderOutput(rawText) {
  const text = rawText || "Sin salida";
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
    input.type = field.kind === "float" ? "number" : "text";
    if (field.kind === "float") {
      input.step = "any";
    }
    input.value = String(field.default ?? "");
  }

  wrapper.appendChild(input);
  return wrapper;
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

function collectParams(method) {
  const params = {};
  for (const field of method.fields) {
    const element = document.getElementById(field.key);
    const value = element.value?.trim();
    if (!value) {
      throw new Error(`El campo '${field.label}' es obligatorio.`);
    }
    if (field.kind === "float") {
      const numeric = Number(value);
      if (Number.isNaN(numeric)) {
        throw new Error(`El campo '${field.label}' debe ser numerico.`);
      }
      params[field.key] = numeric;
    } else {
      params[field.key] = value;
    }
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
    throw new Error(`El parametro global '${label}' debe ser numerico.`);
  }
  if (integer && !Number.isInteger(value)) {
    throw new Error(`El parametro global '${label}' debe ser entero.`);
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

async function renderPlot(points) {
  if (!window.Plotly) {
    setPlotMessage("Plotly no esta disponible.");
    return;
  }

  const series = buildPlotSeries(points);
  const trace = {
    type: "scatter",
    mode: "lines",
    x: series.x,
    y: series.y,
    line: { color: "#0f8b8d", width: 2.3 },
    connectgaps: false,
    hoverdistance: 24,
    hovertemplate: "x=%{x:.6g}<br>y=%{y:.6g}<extra></extra>",
  };

  const hoverTrace = {
    type: "scatter",
    mode: "markers",
    x: [null],
    y: [null],
    marker: { size: 8, color: "#d1495b", line: { color: "#ffffff", width: 1.2 } },
    hoverinfo: "skip",
    showlegend: false,
  };

  const ticks = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5];

  const layout = {
    margin: { l: 58, r: 24, t: 34, b: 48 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "#f7fbfd",
    showlegend: false,
    dragmode: "pan",
    hovermode: "closest",
    xaxis: {
      title: "x",
      showgrid: true,
      gridcolor: "#d9e8ee",
      zeroline: true,
      zerolinecolor: "#355868",
      zerolinewidth: 1.4,
      range: [-5, 5],
      tickmode: "array",
      tickvals: ticks,
      ticktext: ticks.map((value) => String(value)),
      fixedrange: true,
      automargin: true,
    },
    yaxis: {
      title: "y",
      showgrid: true,
      gridcolor: "#d9e8ee",
      zeroline: true,
      zerolinecolor: "#355868",
      zerolinewidth: 1.4,
      range: [-5, 5],
      tickmode: "array",
      tickvals: ticks,
      ticktext: ticks.map((value) => String(value)),
      fixedrange: true,
      automargin: true,
    },
    annotations: [],
  };

  const config = {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["select2d", "lasso2d", "autoScale2d", "toImage"],
    scrollZoom: true,
  };

  await window.Plotly.react(plotlyChart, [trace, hoverTrace], layout, config);

  if (typeof plotlyChart.removeAllListeners === "function") {
    plotlyChart.removeAllListeners("plotly_hover");
    plotlyChart.removeAllListeners("plotly_unhover");
  }

  plotlyChart.on("plotly_hover", (event) => {
    const point = event?.points?.[0];
    if (!point || point.data !== trace || point.x == null || point.y == null) {
      return;
    }
    window.Plotly.restyle(plotlyChart, { x: [[point.x]], y: [[point.y]] }, [1]);
  });

  plotlyChart.on("plotly_unhover", () => {
    window.Plotly.restyle(plotlyChart, { x: [[null]], y: [[null]] }, [1]);
  });

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

    await renderPlot(data.points);
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
    setPlotMessage("Seleccioná un método para graficar.");
    return;
  }

  methodDescription.textContent = method.description;
  methodForm.innerHTML = "";

  for (const field of method.fields) {
    methodForm.appendChild(createInput(field));
  }

  placeLatexPreviewUnderExpressionField();
  applyPersistedMethodInputs(method.key);
  clearPlot();
  setPlotMessage("Esperando ejecución...");
  scheduleLatexPreview();
}

async function runMethod() {
  const method = selectedMethod();
  if (!method) {
    return;
  }

  let params;
  let globalConfig;
  try {
    params = collectParams(method);
    globalConfig = collectGlobalConfig();
  } catch (error) {
    setStatus("error", "Entrada invalida");
    renderOutput(String(error.message || error));
    return;
  }

  setStatus("idle", "Ejecutando");
  renderOutput("Procesando...");

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ method: method.key, params, global_config: globalConfig }),
    });

    const data = await response.json();
    if (!response.ok || !data.success) {
      setStatus("error", "Error");
      renderOutput(data.error || "Error al ejecutar el método.");
      return;
    }

    setStatus("ok", "Correcto");
    renderOutput(data.output || "Sin salida");
    await requestPlot(method, params);
  } catch (error) {
    setStatus("error", "Conexion");
    renderOutput(`No se pudo conectar con el servidor: ${String(error)}`);
  }
}

async function bootstrap() {
  loadPersistedState();
  applyPersistedGlobalInputs();

  setStatus("idle", "Cargando");
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
  persistedState.selectedMethod = methodSelect.value;
  savePersistedState();
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

bootstrap().catch((error) => {
  setStatus("error", "Carga fallida");
  renderOutput(`No se pudieron cargar los métodos: ${String(error)}`);
  clearPlot();
  setPlotMessage(`No se pudo inicializar el gráfico: ${String(error)}`);
});
