from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


app = FastAPI(title="Conversor de unidades")


class ConversionRequest(BaseModel):
    category: str
    value: float = Field(..., description="Valor a convertir")
    from_unit: str
    to_unit: str


LINEAR_UNITS = {
    "longitud": {
        "metro": 1.0,
        "kilometro": 1000.0,
        "centimetro": 0.01,
        "milimetro": 0.001,
        "milla": 1609.344,
        "yarda": 0.9144,
        "pie": 0.3048,
        "pulgada": 0.0254,
    },
    "masa": {
        "kilogramo": 1.0,
        "gramo": 0.001,
        "miligramo": 0.000001,
        "libra": 0.45359237,
        "onza": 0.028349523125,
        "tonelada": 1000.0,
    },
    "volumen": {
        "litro": 1.0,
        "mililitro": 0.001,
        "metro_cubico": 1000.0,
        "galon_us": 3.785411784,
        "taza_us": 0.2365882365,
        "onza_liquida_us": 0.0295735295625,
    },
    "tiempo": {
        "segundo": 1.0,
        "milisegundo": 0.001,
        "minuto": 60.0,
        "hora": 3600.0,
        "dia": 86400.0,
        "semana": 604800.0,
    },
    "velocidad": {
        "metro_por_segundo": 1.0,
        "kilometro_por_hora": 1 / 3.6,
        "milla_por_hora": 0.44704,
        "nudo": 0.514444,
    },
    "area": {
        "metro_cuadrado": 1.0,
        "kilometro_cuadrado": 1_000_000.0,
        "centimetro_cuadrado": 0.0001,
        "hectarea": 10_000.0,
        "acre": 4046.8564224,
        "pie_cuadrado": 0.09290304,
    },
    "datos": {
        "byte": 1.0,
        "kilobyte": 1000.0,
        "megabyte": 1_000_000.0,
        "gigabyte": 1_000_000_000.0,
        "terabyte": 1_000_000_000_000.0,
        "kibibyte": 1024.0,
        "mebibyte": 1024.0 ** 2,
        "gibibyte": 1024.0 ** 3,
    },
}

UNIT_LABELS = {
    "metro": "Metros", "kilometro": "Kilómetros", "centimetro": "Centímetros",
    "milimetro": "Milímetros", "milla": "Millas", "yarda": "Yardas",
    "pie": "Pies", "pulgada": "Pulgadas", "kilogramo": "Kilogramos",
    "gramo": "Gramos", "miligramo": "Miligramos", "libra": "Libras",
    "onza": "Onzas", "tonelada": "Toneladas", "litro": "Litros",
    "mililitro": "Mililitros", "metro_cubico": "Metros cúbicos",
    "galon_us": "Galones US", "taza_us": "Tazas US",
    "onza_liquida_us": "Onzas líquidas US", "segundo": "Segundos",
    "milisegundo": "Milisegundos", "minuto": "Minutos", "hora": "Horas",
    "dia": "Días", "semana": "Semanas", "metro_por_segundo": "Metros/segundo",
    "kilometro_por_hora": "Kilómetros/hora", "milla_por_hora": "Millas/hora",
    "nudo": "Nudos", "metro_cuadrado": "Metros cuadrados",
    "kilometro_cuadrado": "Kilómetros cuadrados",
    "centimetro_cuadrado": "Centímetros cuadrados", "hectarea": "Hectáreas",
    "acre": "Acres", "pie_cuadrado": "Pies cuadrados", "byte": "Bytes",
    "kilobyte": "Kilobytes", "megabyte": "Megabytes", "gigabyte": "Gigabytes",
    "terabyte": "Terabytes", "kibibyte": "Kibibytes",
    "mebibyte": "Mebibytes", "gibibyte": "Gibibytes",
    "celsius": "Celsius", "fahrenheit": "Fahrenheit", "kelvin": "Kelvin",
}

CATEGORY_LABELS = {
    "longitud": "Longitud", "masa": "Masa", "temperatura": "Temperatura",
    "volumen": "Volumen", "tiempo": "Tiempo", "velocidad": "Velocidad",
    "area": "Área", "datos": "Datos",
}


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    if from_unit == "fahrenheit":
        celsius = (value - 32) * 5 / 9
    elif from_unit == "kelvin":
        celsius = value - 273.15
    else:
        celsius = value

    if to_unit == "fahrenheit":
        return celsius * 9 / 5 + 32
    if to_unit == "kelvin":
        return celsius + 273.15
    return celsius


@app.get("/api/units")
def get_units():
    units = {name: [{"id": unit, "label": UNIT_LABELS[unit]} for unit in values]
             for name, values in LINEAR_UNITS.items()}
    units["temperatura"] = [
        {"id": "celsius", "label": "Celsius"},
        {"id": "fahrenheit", "label": "Fahrenheit"},
        {"id": "kelvin", "label": "Kelvin"},
    ]
    return {"categories": [{"id": key, "label": value} for key, value in CATEGORY_LABELS.items()],
            "units": units}


@app.post("/api/convert")
def convert(request: ConversionRequest):
    category = request.category.lower()
    from_unit = request.from_unit.lower()
    to_unit = request.to_unit.lower()

    if category == "temperatura":
        valid_units = {"celsius", "fahrenheit", "kelvin"}
        if from_unit not in valid_units or to_unit not in valid_units:
            raise HTTPException(status_code=400, detail="Unidad de temperatura no válida.")
        result = convert_temperature(request.value, from_unit, to_unit)
    else:
        units = LINEAR_UNITS.get(category)
        if not units:
            raise HTTPException(status_code=400, detail="Categoría no válida.")
        if from_unit not in units or to_unit not in units:
            raise HTTPException(status_code=400, detail="Unidad no válida para esta categoría.")
        result = request.value * units[from_unit] / units[to_unit]

    if abs(result) >= 1_000_000_000 or (0 < abs(result) < 0.000001):
        formatted = format(result, ".6g")
    else:
        formatted = f"{result:.12g}"
    return {"result": result, "formatted": formatted}


@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_PAGE


HTML_PAGE = r"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#e6b84a">
  <title>Medir — Conversor de unidades</title>
  <style>
    :root {
      --ink: #171714;
      --paper: #f3efe4;
      --yellow: #e6b84a;
      --red: #cc4b38;
      --blue: #2f5d73;
      --line: #b9b4a7;
      --muted: #68675f;
      --font-display: Georgia, "Times New Roman", serif;
      --font-ui: "Trebuchet MS", "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        linear-gradient(rgba(23,23,20,.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(23,23,20,.035) 1px, transparent 1px),
        var(--paper);
      background-size: 24px 24px;
      font-family: var(--font-ui);
    }
    button, input, select { font: inherit; }
    .shell { width: min(1180px, calc(100% - 32px)); margin: 0 auto; }
    header {
      height: 88px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 3px solid var(--ink);
    }
    .brand { display: flex; align-items: baseline; gap: 12px; }
    .brand-mark {
      width: 44px; height: 44px; display: grid; place-items: center;
      border: 3px solid var(--ink); background: var(--yellow);
      border-radius: 50%; font: 700 20px/1 Georgia, serif;
    }
    .brand-name { font: 700 32px/1 var(--font-display); letter-spacing: -1px; }
    .edition { color: var(--muted); font-size: 12px; letter-spacing: 2px; text-transform: uppercase; }
    main { padding: 42px 0 32px; }
    .intro { display: grid; grid-template-columns: 1fr auto; align-items: end; margin-bottom: 28px; }
    h1 { margin: 0; max-width: 760px; font: 700 clamp(44px, 7vw, 82px)/.92 var(--font-display); letter-spacing: -4px; }
    .intro-index { font: 700 17px/1 var(--font-ui); border-top: 2px solid var(--ink); padding-top: 10px; }
    .workspace {
      display: grid;
      grid-template-columns: 220px minmax(0, 1fr);
      border: 3px solid var(--ink);
      background: rgba(243,239,228,.94);
      box-shadow: 10px 10px 0 var(--ink);
    }
    .categories {
      border-right: 3px solid var(--ink);
      background: var(--ink);
      padding: 10px;
    }
    .category-btn {
      width: 100%; min-height: 48px; margin-bottom: 6px;
      border: 0; border-bottom: 1px solid #4b4b44;
      color: #f7f2e6; background: transparent;
      text-align: left; padding: 10px 12px;
      cursor: pointer; font-weight: 700;
      display: flex; justify-content: space-between; align-items: center;
    }
    .category-btn span { opacity: .5; font-size: 12px; }
    .category-btn:hover { background: #30302b; }
    .category-btn.active { background: var(--yellow); color: var(--ink); border: 0; }
    .category-btn:focus-visible, .swap-btn:focus-visible, input:focus-visible, select:focus-visible {
      outline: 3px solid var(--red); outline-offset: 3px;
    }
    .converter { padding: clamp(24px, 4vw, 48px); }
    .category-heading {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 24px; padding-bottom: 12px; border-bottom: 1px solid var(--line);
    }
    .category-heading h2 { margin: 0; font: 700 28px/1 var(--font-display); }
    .status { color: var(--muted); font-size: 12px; letter-spacing: 1px; text-transform: uppercase; }
    .conversion-grid { display: grid; grid-template-columns: minmax(0, 1fr) 74px minmax(0, 1fr); align-items: end; gap: 16px; }
    .field label { display: block; margin-bottom: 8px; font-size: 12px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; }
    input, select {
      width: 100%; height: 64px; border: 2px solid var(--ink);
      border-radius: 0; background: #fffdf6; color: var(--ink);
    }
    input { margin-bottom: 10px; padding: 8px 14px; font: 700 clamp(24px, 4vw, 38px)/1 var(--font-display); }
    select { padding: 0 42px 0 14px; cursor: pointer; font-weight: 700; }
    input[readonly] { background: var(--yellow); }
    .swap-wrap { height: 64px; display: grid; place-items: center; }
    .swap-btn {
      width: 58px; height: 58px; border: 2px solid var(--ink); border-radius: 50%;
      background: var(--paper); color: var(--ink); cursor: pointer; font-size: 24px;
      box-shadow: 4px 4px 0 var(--ink); transition: transform .15s ease, box-shadow .15s ease;
    }
    .swap-btn:hover { transform: translate(-2px, -2px); box-shadow: 6px 6px 0 var(--ink); }
    .swap-btn:active { transform: translate(2px, 2px); box-shadow: 2px 2px 0 var(--ink); }
    .result-line { margin-top: 28px; min-height: 24px; color: var(--muted); font-size: 14px; }
    .error { color: #9f2f20; font-weight: 700; }
    footer { height: 70px; display: flex; align-items: end; justify-content: space-between; color: var(--muted); font-size: 12px; }
    @media (max-width: 760px) {
      .shell { width: min(100% - 20px, 1180px); }
      header { height: 72px; }
      .edition { display: none; }
      main { padding-top: 28px; }
      h1 { letter-spacing: -2px; }
      .intro-index { display: none; }
      .workspace { grid-template-columns: 1fr; box-shadow: 6px 6px 0 var(--ink); }
      .categories { display: flex; overflow-x: auto; border-right: 0; border-bottom: 3px solid var(--ink); padding: 8px; }
      .category-btn { width: auto; min-width: 112px; margin: 0 6px 0 0; border: 0; text-align: center; justify-content: center; }
      .category-btn span { display: none; }
      .conversion-grid { grid-template-columns: 1fr; }
      .swap-wrap { height: 44px; }
      .swap-btn { width: 44px; height: 44px; transform: rotate(90deg); }
      .swap-btn:hover { transform: rotate(90deg) translate(-2px, -2px); }
      footer { height: 58px; }
    }
    @media (prefers-reduced-motion: reduce) {
      * { scroll-behavior: auto !important; transition: none !important; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div class="brand"><div class="brand-mark">M</div><div class="brand-name">MEDIR</div></div>
      <div class="edition">Conversión práctica · 2026</div>
    </header>
    <main>
      <div class="intro">
        <h1>Convierte<br>sin rodeos.</h1>
        <div class="intro-index">SERIE 01 / 08</div>
      </div>
      <section class="workspace" aria-label="Conversor de unidades">
        <nav class="categories" id="categories" aria-label="Categorías"></nav>
        <div class="converter">
          <div class="category-heading">
            <h2 id="categoryTitle">Longitud</h2>
            <div class="status" id="status">LISTO</div>
          </div>
          <div class="conversion-grid">
            <div class="field">
              <label for="fromValue">Cantidad</label>
              <input id="fromValue" type="number" step="any" value="1" inputmode="decimal">
              <label class="sr-only" for="fromUnit">Unidad de origen</label>
              <select id="fromUnit"></select>
            </div>
            <div class="swap-wrap">
              <button class="swap-btn" id="swapBtn" type="button" aria-label="Intercambiar unidades">⇄</button>
            </div>
            <div class="field">
              <label for="toValue">Resultado</label>
              <input id="toValue" type="text" readonly value="—">
              <label class="sr-only" for="toUnit">Unidad de destino</label>
              <select id="toUnit"></select>
            </div>
          </div>
          <div class="result-line" id="resultLine" aria-live="polite"></div>
        </div>
      </section>
    </main>
    <footer><span>MEDIR / HERRAMIENTAS</span><span id="precision">Precisión 12 dígitos</span></footer>
  </div>
  <script>
    let unitsByCategory = {};
    let categories = [];
    let activeCategory = "longitud";

    const categoriesEl = document.getElementById("categories");
    const categoryTitle = document.getElementById("categoryTitle");
    const fromValue = document.getElementById("fromValue");
    const toValue = document.getElementById("toValue");
    const fromUnit = document.getElementById("fromUnit");
    const toUnit = document.getElementById("toUnit");
    const status = document.getElementById("status");
    const resultLine = document.getElementById("resultLine");
    const swapBtn = document.getElementById("swapBtn");

    async function load() {
      try {
        const response = await fetch("/api/units");
        if (!response.ok) throw new Error("No se pudieron cargar las unidades");
        const data = await response.json();
        categories = data.categories;
        unitsByCategory = data.units;
        renderCategories();
        setCategory(activeCategory);
      } catch (error) {
        showError(error.message);
      }
    }

    function renderCategories() {
      categoriesEl.innerHTML = "";
      categories.forEach((category, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "category-btn";
        button.dataset.category = category.id;
        button.innerHTML = `${category.label}<span>${String(index + 1).padStart(2, "0")}</span>`;
        button.addEventListener("click", () => setCategory(category.id));
        categoriesEl.appendChild(button);
      });
    }

    function setCategory(category) {
      activeCategory = category;
      document.querySelectorAll(".category-btn").forEach(button => {
        button.classList.toggle("active", button.dataset.category === category);
      });
      const categoryInfo = categories.find(item => item.id === category);
      categoryTitle.textContent = categoryInfo ? categoryInfo.label : category;
      const units = unitsByCategory[category] || [];
      fillSelect(fromUnit, units);
      fillSelect(toUnit, units);
      if (units.length > 1) toUnit.selectedIndex = 1;
      convert();
    }

    function fillSelect(select, units) {
      select.innerHTML = units.map(unit => `<option value="${unit.id}">${unit.label}</option>`).join("");
    }

    async function convert() {
      const rawValue = fromValue.value.trim();
      resultLine.className = "result-line";
      if (rawValue === "") {
        toValue.value = "—";
        resultLine.textContent = "Introduce una cantidad.";
        status.textContent = "ESPERANDO";
        return;
      }
      const value = Number(rawValue);
      if (!Number.isFinite(value)) {
        showError("Introduce un número válido.");
        return;
      }
      status.textContent = "CALCULANDO";
      try {
        const response = await fetch("/api/convert", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            category: activeCategory,
            value,
            from_unit: fromUnit.value,
            to_unit: toUnit.value
          })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "No se pudo realizar la conversión");
        toValue.value = data.formatted;
        const origin = fromUnit.options[fromUnit.selectedIndex].text;
        const destination = toUnit.options[toUnit.selectedIndex].text;
        resultLine.text = "";
        resultLine.textContent = `${rawValue} ${origin} = ${data.formatted} ${destination}`;
        status.textContent = "CONVERTIDO";
      } catch (error) {
        showError(error.message);
      }
    }

    function showError(message) {
      toValue.value = "—";
      resultLine.textContent = message;
      resultLine.className = "result-line error";
      status.textContent = "REVISAR";
    }

    let debounce;
    fromValue.addEventListener("input", () => {
      clearTimeout(debounce);
      debounce = setTimeout(convert, 120);
    });
    fromUnit.addEventListener("change", convert);
    toUnit.addEventListener("change", convert);
    swapBtn.addEventListener("click", () => {
      const oldFrom = fromUnit.value;
      fromUnit.value = toUnit.value;
      toUnit.value = oldFrom;
      convert();
    });

    load();
  </script>
  <style>
    .sr-only {
      position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
      overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;
    }
  </style>
</body>
</html>"""
