const defaultConfig = {
  room: {
    name: "Main bedroom",
    length_m: 5.0,
    width_m: 4.0,
    height_m: 2.7,
    mixing_effectiveness: 0.85
  },
  particle: {
    target_clean_ach: 5.0,
    existing_removal_ach: 0.3,
    single_pass_efficiency: 0.97
  },
  formaldehyde: {
    target_clean_ach: 2.0,
    existing_removal_ach: 0.1,
    target_concentration_ug_m3: 60.0,
    source_generation_ug_h: 500.0,
    outdoor_concentration_ug_m3: 5.0,
    ventilation_m3h: 20.0,
    single_pass_efficiency: 0.55,
    first_order_rate_s: null,
    carbon_bed_depth_m: 0.0,
    bed_porosity: 0.45,
    challenge_concentration_ug_m3: 80.0,
    carbon_mass_g: 900.0,
    capacity_mg_per_g: 12.0,
    capacity_utilization: 0.55,
    temperature_c: 25.0,
    relative_humidity_percent: 60.0
  },
  filter: {
    media_velocity_limit_m_s: 0.22,
    pleat_area_multiplier: 8.0,
    fixed_media_area_m2: null,
    frontal_width_m: null,
    frontal_height_m: null,
    bypass_fraction: 0.03,
    pressure_drop_ref_pa: 55.0,
    pressure_drop_ref_velocity_m_s: 0.20,
    pressure_drop_exponent: 1.35,
    loaded_pressure_drop_multiplier: 1.8
  },
  fan: {
    free_airflow_m3h: 430.0,
    shutoff_pressure_pa: 210.0,
    system_pressure_pa: 18.0,
    curve_exponent: 1.7,
    fixed_airflow_m3h: null,
    power_w: 45.0
  },
  safety_factor: 1.15
};

let latestPayload = null;
let latestResult = null;
let tooltipElement = null;

const mm2PerM2 = 1000000;
const mmPerM = 1000;

const inputConversions = {
  "filter.fixed_media_area_m2": {
    toUi: (value) => value * mm2PerM2,
    fromUi: (value) => value / mm2PerM2
  },
  "filter.frontal_width_m": {
    toUi: (value) => value * mmPerM,
    fromUi: (value) => value / mmPerM
  },
  "filter.frontal_height_m": {
    toUi: (value) => value * mmPerM,
    fromUi: (value) => value / mmPerM
  }
};

const fieldHelp = {
  "room.name": "A label for this room or test case.",
  "room.length_m": "Room internal length in metres. Used with width and height to calculate room volume.",
  "room.width_m": "Room internal width in metres. Used to calculate floor area and volume.",
  "room.height_m": "Room internal height in metres. Typical homes are about 2.4 to 3.0 m.",
  "room.mixing_effectiveness": "How well clean air mixes in the room. Use 1.0 for ideal mixing; 0.7 to 0.9 is common for real placement.",
  "particle.target_clean_ach": "Target equivalent clean air changes per hour for particle removal.",
  "particle.existing_removal_ach": "Particle removal already provided by deposition, ventilation, or other systems.",
  "particle.single_pass_efficiency": "Fraction of particles captured in one pass through the filter. Use a decimal, for example 0.97.",
  "formaldehyde.target_clean_ach": "Target equivalent clean air changes per hour for formaldehyde removal.",
  "formaldehyde.existing_removal_ach": "Formaldehyde removal already provided by ventilation, surface loss, or other systems.",
  "formaldehyde.target_concentration_ug_m3": "Indoor formaldehyde concentration target in micrograms per cubic metre.",
  "formaldehyde.source_generation_ug_h": "Estimated continuous formaldehyde emission rate from furniture, finishes, or materials.",
  "formaldehyde.outdoor_concentration_ug_m3": "Outdoor formaldehyde concentration entering through ventilation.",
  "formaldehyde.ventilation_m3h": "Outdoor air ventilation flow rate into the room.",
  "formaldehyde.single_pass_efficiency": "Fraction of formaldehyde removed in one pass through the gas media. Use supplier or test data when possible.",
  "formaldehyde.first_order_rate_s": "Optional gas-media kinetic rate. Leave blank when using measured single-pass efficiency.",
  "formaldehyde.carbon_bed_depth_m": "Activated carbon or gas-media bed depth in metres. Used only with kinetic-rate estimation.",
  "formaldehyde.bed_porosity": "Void fraction of the gas-media bed. Typical packed beds are often around 0.35 to 0.55.",
  "formaldehyde.challenge_concentration_ug_m3": "Formaldehyde concentration used for capacity and capture-rate estimates.",
  "formaldehyde.carbon_mass_g": "Mass of activated carbon or gas adsorbent in grams.",
  "formaldehyde.capacity_mg_per_g": "Usable formaldehyde holding capacity per gram of adsorbent before breakthrough.",
  "formaldehyde.capacity_utilization": "Fraction of theoretical capacity expected to be usable in the product.",
  "formaldehyde.temperature_c": "Operating air temperature in Celsius.",
  "formaldehyde.relative_humidity_percent": "Operating relative humidity. High humidity can reduce formaldehyde adsorption.",
  "filter.fixed_media_area_m2": "Known unfolded filter media area in mm2. Use this only when the supplier gives actual media area.",
  "filter.frontal_width_m": "Visible filter opening width in mm, measured across the front face.",
  "filter.frontal_height_m": "Visible filter opening height in mm, measured across the front face.",
  "filter.media_velocity_limit_m_s": "Maximum air velocity through the media. Lower values reduce pressure drop and can improve efficiency.",
  "filter.pleat_area_multiplier": "How many times larger the pleated media area is than the frontal area. Use 1 for a flat filter.",
  "filter.bypass_fraction": "Fraction of airflow leaking around the filter instead of passing through it.",
  "filter.pressure_drop_ref_pa": "Clean filter pressure drop measured at the reference media velocity.",
  "filter.pressure_drop_ref_velocity_m_s": "Media velocity used for the reference pressure-drop value.",
  "filter.pressure_drop_exponent": "Pressure-drop scaling exponent. Around 1.0 is linear; many filters are about 1.2 to 1.6.",
  "filter.loaded_pressure_drop_multiplier": "End-of-life pressure-drop multiplier compared with the clean filter.",
  "fan.free_airflow_m3h": "Fan airflow at zero pressure drop.",
  "fan.shutoff_pressure_pa": "Maximum static pressure when fan airflow is zero.",
  "fan.curve_exponent": "Shape of the fan pressure-flow curve. Use about 1.5 to 2.0 when exact data is unknown.",
  "fan.fixed_airflow_m3h": "Known delivered airflow through the filter when using fixed-flow mode.",
  "fan.system_pressure_pa": "Additional housing, grille, duct, and outlet pressure losses besides the filter.",
  "fan.power_w": "Electrical fan power in watts. Used for reporting.",
  "safety_factor": "Multiplier applied to required CADR during sizing. Use above 1.0 to add design margin."
};

document.addEventListener("DOMContentLoaded", () => {
  applyFieldHelp();
  setForm(defaultConfig);
  updateFanMode();
  updateFilterSizeMode();
  updateComputedMediaArea();
  document.querySelectorAll("input[name='fan-mode']").forEach((input) => {
    input.addEventListener("change", updateFanMode);
  });
  document.querySelectorAll("input[name='filter-size-mode']").forEach((input) => {
    input.addEventListener("change", updateFilterSizeMode);
  });
  document.querySelectorAll("input[name='filter-input-mode']").forEach((input) => {
    input.addEventListener("change", updateFilterSizeMode);
  });
  [
    "filter.frontal_width_m",
    "filter.frontal_height_m",
    "filter.pleat_area_multiplier"
  ].forEach((path) => {
    const input = document.querySelector(`[data-path='${path}']`);
    if (input) {
      input.addEventListener("input", updateComputedMediaArea);
    }
  });
  document.getElementById("calculate-button").addEventListener("click", calculate);
  document.getElementById("reset-button").addEventListener("click", () => {
    setForm(defaultConfig);
    updateFanMode();
    updateFilterSizeMode();
    updateComputedMediaArea();
    calculate();
  });
  document.getElementById("export-button").addEventListener("click", exportJson);
  calculate();
});

function setForm(config) {
  document.querySelectorAll("[data-path]").forEach((input) => {
    const path = input.dataset.path;
    const conversion = inputConversions[path];
    const rawValue = getPath(config, path);
    const value = rawValue === null || rawValue === undefined || !conversion ? rawValue : conversion.toUi(rawValue);
    input.value = value === null || value === undefined ? "" : value;
  });
  const fixed = config.fan && config.fan.fixed_airflow_m3h;
  document.querySelector(`input[name='fan-mode'][value='${fixed ? "fixed" : "curve"}']`).checked = true;
  const fixedFilter = config.filter && (
    config.filter.fixed_media_area_m2 ||
    (config.filter.frontal_width_m && config.filter.frontal_height_m)
  );
  document.querySelector(`input[name='filter-size-mode'][value='${fixedFilter ? "fixed" : "sizing"}']`).checked = true;
  const inputMode = config.filter && config.filter.fixed_media_area_m2 ? "media-area" : "dimensions";
  document.querySelector(`input[name='filter-input-mode'][value='${inputMode}']`).checked = true;
}

function readForm() {
  const payload = {};
  document.querySelectorAll("[data-path]").forEach((input) => {
    const path = input.dataset.path;
    const conversion = inputConversions[path];
    const rawValue = input.type === "number" ? numberOrNull(input.value) : input.value;
    const value = rawValue === null || !conversion ? rawValue : conversion.fromUi(rawValue);
    setPath(payload, path, value);
  });

  const mode = document.querySelector("input[name='fan-mode']:checked").value;
  if (mode === "curve") {
    payload.fan.fixed_airflow_m3h = null;
  } else {
    payload.fan.free_airflow_m3h = null;
    payload.fan.shutoff_pressure_pa = null;
  }

  const filterMode = document.querySelector("input[name='filter-size-mode']:checked").value;
  if (filterMode === "sizing") {
    payload.filter.fixed_media_area_m2 = null;
    payload.filter.frontal_width_m = null;
    payload.filter.frontal_height_m = null;
  } else {
    const inputMode = document.querySelector("input[name='filter-input-mode']:checked").value;
    if (inputMode === "dimensions") {
      payload.filter.fixed_media_area_m2 = null;
      if (!payload.filter.frontal_width_m || !payload.filter.frontal_height_m) {
        throw new Error("Enter frontal width and frontal height to evaluate a filter by dimensions.");
      }
    } else {
      payload.filter.frontal_width_m = null;
      payload.filter.frontal_height_m = null;
      if (!payload.filter.fixed_media_area_m2) {
        throw new Error("Enter known media area to evaluate a filter by media area.");
      }
    }
  }
  return payload;
}

async function calculate() {
  const button = document.getElementById("calculate-button");
  setStatus("Calculating...");
  button.disabled = true;
  try {
    const payload = readForm();
    const response = await fetch("/api/design", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Calculation failed");
    }
    latestPayload = data.inputs;
    latestResult = data.result;
    renderResults(latestPayload, latestResult);
    setStatus("Ready");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    button.disabled = false;
  }
}

function renderResults(inputs, result) {
  renderMetrics(result);
  renderSummary(inputs, result);
  renderCadrChart(result);
  renderFanChart(inputs, result);
  renderAreaChart(inputs, result);
  renderDecayChart(inputs, result);
  renderCapacityChart(inputs, result);
}

function renderMetrics(result) {
  const metrics = [
    [
      "Loaded P-CADR",
      fmt(result.loaded_p_cadr_m3h, 1),
      "m3/h",
      "Particle clean-air delivery with a loaded filter: airflow x particle efficiency x bypass correction x room mixing."
    ],
    [
      "Loaded F-CADR",
      fmt(result.loaded_f_cadr_m3h, 1),
      "m3/h",
      "Formaldehyde clean-air delivery with a loaded filter: airflow x gas-media efficiency x bypass correction x room mixing."
    ],
    [
      "Media area",
      fmt(result.required_media_area_m2 * mm2PerM2, 0),
      "mm2",
      "Unfolded filter media area used. With dimensions: frontal width x frontal height x pleat multiplier."
    ],
    [
      "Pressure margin",
      result.pressure_margin_at_design_pa === null ? "Fixed" : fmt(result.pressure_margin_at_design_pa, 1),
      "Pa at design flow",
      "Fan pressure available at design airflow minus loaded system pressure. Positive margin means the fan can meet the pressure demand."
    ],
    [
      "Loaded P-ACH",
      fmt(result.loaded_p_ach, 2),
      "1/h",
      "Particle equivalent clean air changes per hour: loaded P-CADR divided by room volume."
    ],
    [
      "Loaded F-ACH",
      fmt(result.loaded_f_ach, 2),
      "1/h",
      "Formaldehyde equivalent clean air changes per hour: loaded F-CADR divided by room volume."
    ],
    [
      "Particle 80% time",
      fmt(result.p_time_to_80_percent_reduction_min, 1),
      "min",
      "Estimated time for particle concentration to fall to 20% of the starting level using loaded P-CADR and existing removal."
    ],
    [
      "HCHO life",
      result.formaldehyde_service_life_h === null ? "N/A" : fmt(result.formaldehyde_service_life_h, 0),
      "operating h",
      "Estimated gas-media operating life from carbon mass, usable HCHO capacity, airflow, concentration, and capture efficiency."
    ]
  ];
  document.getElementById("metrics").innerHTML = metrics.map(([label, value, sub, explanation]) => `
    <div class="metric">
      <div class="label">${escapeHtml(label)}</div>
      <div class="value">${escapeHtml(value)}</div>
      <div class="sub">${escapeHtml(sub)}</div>
      <div class="explain">${escapeHtml(explanation)}</div>
    </div>
  `).join("");
}

function renderSummary(inputs, result) {
  const warnings = result.warnings && result.warnings.length
    ? `<div class="warnings">${result.warnings.map((warning) => `<div>${escapeHtml(warning)}</div>`).join("")}</div>`
    : "";
  document.getElementById("summary").innerHTML = `
    <table class="summary-table">
      <thead>
        <tr><th>Metric</th><th>Required</th><th>Clean</th><th>Loaded</th></tr>
      </thead>
      <tbody>
        <tr>
          <td>P-CADR, m3/h</td>
          <td>${fmt(result.required_p_cadr_m3h, 1)}</td>
          <td>${fmt(result.clean_p_cadr_m3h, 1)}</td>
          <td>${fmt(result.loaded_p_cadr_m3h, 1)}</td>
        </tr>
        <tr>
          <td>F-CADR, m3/h</td>
          <td>${fmt(result.required_f_cadr_m3h, 1)}</td>
          <td>${fmt(result.clean_f_cadr_m3h, 1)}</td>
          <td>${fmt(result.loaded_f_cadr_m3h, 1)}</td>
        </tr>
        <tr>
          <td>Airflow, m3/h</td>
          <td>${fmt(result.design_airflow_m3h, 1)}</td>
          <td>${fmt(result.clean_airflow_m3h, 1)}</td>
          <td>${fmt(result.loaded_airflow_m3h, 1)}</td>
        </tr>
        <tr>
          <td>Media area, mm2</td>
          <td>${fmt(result.minimum_required_media_area_m2 * mm2PerM2, 0)}</td>
          <td colspan="2">${fmt(result.required_media_area_m2 * mm2PerM2, 0)} used</td>
        </tr>
        <tr>
          <td>Pressure drop, Pa</td>
          <td>${result.fan_available_pressure_at_design_pa === null ? "Fixed flow" : fmt(result.fan_available_pressure_at_design_pa, 1)}</td>
          <td>${fmt(result.clean_pressure_drop_pa, 1)}</td>
          <td>${fmt(result.loaded_pressure_drop_pa, 1)}</td>
        </tr>
      </tbody>
    </table>
    <p class="warnings">Media basis: ${escapeHtml(result.media_area_basis)}. Room volume: ${fmt(result.room_volume_m3, 2)} m3. Frontal area: ${fmt(result.frontal_area_m2 * mm2PerM2, 0)} mm2. Formaldehyde efficiency used: ${fmt(result.formaldehyde_efficiency_used, 3)}.</p>
    ${warnings}
  `;
}

function renderCadrChart(result) {
  groupedBarChart("cadr-chart", {
    title: "",
    groups: ["P-CADR", "F-CADR"],
    yLabel: "CADR (m3/h)",
    series: [
      { name: "Required", color: "#525252", values: [result.required_p_cadr_m3h, result.required_f_cadr_m3h] },
      { name: "Clean", color: "#2563eb", values: [result.clean_p_cadr_m3h, result.clean_f_cadr_m3h] },
      { name: "Loaded", color: "#168a5b", values: [result.loaded_p_cadr_m3h, result.loaded_f_cadr_m3h] }
    ]
  });
}

function renderFanChart(inputs, result) {
  const fan = inputs.fan;
  const filter = inputs.filter;
  const maxFlow = fan.free_airflow_m3h || result.design_airflow_m3h * 1.4;
  const x = range(0, maxFlow, 100);
  const series = [
    {
      name: "Clean system",
      color: "#2563eb",
      values: x.map((q) => systemPressure(fan, filter, q, result.required_media_area_m2, false))
    },
    {
      name: "Loaded system",
      color: "#d9483b",
      values: x.map((q) => systemPressure(fan, filter, q, result.required_media_area_m2, true))
    }
  ];
  if (fan.free_airflow_m3h && fan.shutoff_pressure_pa) {
    series.push({
      name: "Fan curve",
      color: "#111111",
      values: x.map((q) => fanPressure(fan, q))
    });
  }
  lineChart("fan-chart", {
    x,
    series,
    xLabel: "Airflow (m3/h)",
    yLabel: "Pressure (Pa)",
    markers: [
      { x: result.clean_airflow_m3h, y: result.clean_pressure_drop_pa, color: "#2563eb", label: "Clean" },
      { x: result.loaded_airflow_m3h, y: result.loaded_pressure_drop_pa, color: "#d9483b", label: "Loaded" }
    ]
  });
}

function renderAreaChart(inputs, result) {
  const filter = inputs.filter;
  const x = range(0.08, 0.40, 64);
  const area = x.map((v) => result.design_airflow_m3h / 3600 / v * mm2PerM2);
  const cleanDp = x.map((v) => filter.pressure_drop_ref_pa * Math.pow(v / filter.pressure_drop_ref_velocity_m_s, filter.pressure_drop_exponent));
  const loadedDp = cleanDp.map((value) => value * filter.loaded_pressure_drop_multiplier);
  lineChart("area-chart", {
    x,
    series: [
      { name: "Media area", color: "#2563eb", values: area },
      { name: "Clean delta P", color: "#168a5b", values: cleanDp, axis: "right" },
      { name: "Loaded delta P", color: "#d9483b", values: loadedDp, axis: "right", dash: "6 4" }
    ],
    xLabel: "Media velocity (m/s)",
    yLabel: "Media area (mm2)",
    y2Label: "Filter delta P (Pa)",
    vlines: [{ x: filter.media_velocity_limit_m_s, color: "#525252", label: "Limit" }]
  });
}

function renderDecayChart(inputs, result) {
  const x = range(0, 180, 180);
  const volume = result.room_volume_m3;
  const pNatural = inputs.particle.existing_removal_ach;
  const pTotal = pNatural + result.loaded_p_cadr_m3h / volume;
  const fNatural = inputs.formaldehyde.existing_removal_ach;
  const fTotal = fNatural + result.loaded_f_cadr_m3h / volume;
  lineChart("decay-chart", {
    x,
    yMin: 0,
    yMax: 1,
    series: [
      { name: "Particle natural", color: "#8a8f98", values: x.map((t) => Math.exp(-pNatural * t / 60)) },
      { name: "Particle purifier", color: "#2563eb", values: x.map((t) => Math.exp(-pTotal * t / 60)) },
      { name: "HCHO natural", color: "#b7bdc5", values: x.map((t) => Math.exp(-fNatural * t / 60)), dash: "6 4" },
      { name: "HCHO purifier", color: "#168a5b", values: x.map((t) => Math.exp(-fTotal * t / 60)) }
    ],
    xLabel: "Time (min)",
    yLabel: "Fraction remaining",
    hlines: [{ y: 0.2, color: "#525252", label: "80%" }]
  });
}

function renderCapacityChart(inputs, result) {
  const hcho = inputs.formaldehyde;
  const capacity = hcho.carbon_mass_g * hcho.capacity_mg_per_g * hcho.capacity_utilization;
  if (!result.formaldehyde_capture_rate_mg_h || capacity <= 0) {
    document.getElementById("capacity-chart").innerHTML = `<div class="status">Capacity data incomplete</div>`;
    return;
  }
  const life = result.formaldehyde_service_life_h || 0;
  const maxHours = Math.max(life * 1.1, 24);
  const x = range(0, maxHours, 100);
  const captured = x.map((hour) => Math.min(capacity, hour * result.formaldehyde_capture_rate_mg_h));
  const remaining = captured.map((value) => Math.max(0, capacity - value));
  lineChart("capacity-chart", {
    x,
    series: [
      { name: "Captured HCHO", color: "#d9483b", values: captured },
      { name: "Remaining capacity", color: "#168a5b", values: remaining }
    ],
    xLabel: "Operating hours",
    yLabel: "Mass (mg)",
    vlines: [{ x: life, color: "#525252", label: "Life" }]
  });
}

function groupedBarChart(targetId, options) {
  const width = 760;
  const height = 330;
  const margin = { left: 64, right: 20, top: 18, bottom: 56 };
  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;
  const maxY = niceMax(Math.max(...options.series.flatMap((item) => item.values)));
  const y = (value) => margin.top + plotH - value / maxY * plotH;
  const groupW = plotW / options.groups.length;
  const barW = groupW / (options.series.length + 1.3);
  let svg = svgStart(width, height);
  svg += grid(width, height, margin, maxY, options.yLabel);
  options.groups.forEach((group, groupIndex) => {
    const center = margin.left + groupW * (groupIndex + 0.5);
    const start = center - (barW * options.series.length) / 2;
    svg += text(center, height - 24, group, 12, "middle", "#4b5563");
    options.series.forEach((item, seriesIndex) => {
      const value = item.values[groupIndex];
      const barX = start + seriesIndex * barW;
      const barY = y(value);
      svg += `<rect x="${barX.toFixed(1)}" y="${barY.toFixed(1)}" width="${(barW * 0.82).toFixed(1)}" height="${(margin.top + plotH - barY).toFixed(1)}" fill="${item.color}"></rect>`;
      svg += text(barX + barW * 0.41, barY - 6, fmt(value, 0), 11, "middle", "#374151");
    });
  });
  svg += legend(options.series, width - 178, margin.top + 16);
  svg += "</svg>";
  document.getElementById(targetId).innerHTML = svg;
}

function lineChart(targetId, options) {
  const width = 760;
  const height = 330;
  const margin = { left: 64, right: options.y2Label ? 68 : 22, top: 18, bottom: 56 };
  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;
  const xMin = Math.min(...options.x);
  const xMax = Math.max(...options.x);
  const leftSeries = options.series.filter((item) => item.axis !== "right");
  const rightSeries = options.series.filter((item) => item.axis === "right");
  const yMin = options.yMin ?? 0;
  const yMax = options.yMax ?? niceMax(Math.max(...leftSeries.flatMap((item) => item.values), 1));
  const y2Max = rightSeries.length ? niceMax(Math.max(...rightSeries.flatMap((item) => item.values), 1)) : yMax;
  const xScale = (value) => margin.left + (value - xMin) / (xMax - xMin || 1) * plotW;
  const yScale = (value, max, min = 0) => margin.top + plotH - (value - min) / (max - min || 1) * plotH;
  let svg = svgStart(width, height);
  svg += grid(width, height, margin, yMax, options.yLabel, yMin, options.y2Label, y2Max);
  svg += xTicks(xMin, xMax, margin, plotW, height);
  (options.hlines || []).forEach((line) => {
    const y = yScale(line.y, yMax, yMin);
    svg += `<line x1="${margin.left}" x2="${margin.left + plotW}" y1="${y.toFixed(1)}" y2="${y.toFixed(1)}" stroke="${line.color}" stroke-dasharray="3 4"></line>`;
    svg += text(margin.left + plotW - 4, y - 6, line.label, 11, "end", line.color);
  });
  (options.vlines || []).forEach((line) => {
    const x = xScale(line.x);
    svg += `<line x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${margin.top}" y2="${margin.top + plotH}" stroke="${line.color}" stroke-dasharray="4 4"></line>`;
    svg += text(x + 5, margin.top + 14, line.label, 11, "start", line.color);
  });
  options.series.forEach((item) => {
    const max = item.axis === "right" ? y2Max : yMax;
    const min = item.axis === "right" ? 0 : yMin;
    const points = options.x.map((xValue, index) => `${xScale(xValue).toFixed(1)},${yScale(item.values[index], max, min).toFixed(1)}`).join(" ");
    const dash = item.dash ? ` stroke-dasharray="${item.dash}"` : "";
    svg += `<polyline points="${points}" fill="none" stroke="${item.color}" stroke-width="2.4"${dash}></polyline>`;
  });
  (options.markers || []).forEach((marker) => {
    const x = xScale(marker.x);
    const y = yScale(marker.y, yMax, yMin);
    svg += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4.8" fill="${marker.color}" stroke="#ffffff" stroke-width="1.5"></circle>`;
    svg += text(x + 7, y - 8, marker.label, 11, "start", marker.color);
  });
  svg += legend(options.series, width - margin.right - 176, margin.top + 16);
  svg += "</svg>";
  document.getElementById(targetId).innerHTML = svg;
}

function grid(width, height, margin, yMax, yLabel, yMin = 0, y2Label = null, y2Max = null) {
  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;
  let svg = `<rect x="${margin.left}" y="${margin.top}" width="${plotW}" height="${plotH}" fill="#fbfcfd" stroke="#d9dee5"></rect>`;
  for (let i = 0; i <= 5; i += 1) {
    const value = yMin + (yMax - yMin) * i / 5;
    const y = margin.top + plotH - (value - yMin) / (yMax - yMin || 1) * plotH;
    svg += `<line x1="${margin.left}" x2="${margin.left + plotW}" y1="${y.toFixed(1)}" y2="${y.toFixed(1)}" stroke="#e8edf2"></line>`;
    svg += text(margin.left - 9, y + 4, fmt(value, value >= 10 ? 0 : 2), 11, "end", "#5f6b77");
    if (y2Label && y2Max !== null) {
      svg += text(margin.left + plotW + 9, y + 4, fmt(y2Max * i / 5, 0), 11, "start", "#5f6b77");
    }
  }
  svg += `<line x1="${margin.left}" x2="${margin.left}" y1="${margin.top}" y2="${margin.top + plotH}" stroke="#717b86"></line>`;
  svg += `<line x1="${margin.left}" x2="${margin.left + plotW}" y1="${margin.top + plotH}" y2="${margin.top + plotH}" stroke="#717b86"></line>`;
  svg += `<text x="18" y="${margin.top + plotH / 2}" transform="rotate(-90 18 ${margin.top + plotH / 2})" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="#374151" text-anchor="middle">${escapeHtml(yLabel)}</text>`;
  if (y2Label) {
    svg += `<text x="${width - 18}" y="${margin.top + plotH / 2}" transform="rotate(90 ${width - 18} ${margin.top + plotH / 2})" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="#374151" text-anchor="middle">${escapeHtml(y2Label)}</text>`;
  }
  return svg;
}

function xTicks(xMin, xMax, margin, plotW, height) {
  let svg = "";
  for (let i = 0; i <= 5; i += 1) {
    const value = xMin + (xMax - xMin) * i / 5;
    const x = margin.left + (value - xMin) / (xMax - xMin || 1) * plotW;
    svg += `<line x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${height - margin.bottom}" y2="${height - margin.bottom + 5}" stroke="#717b86"></line>`;
    svg += text(x, height - margin.bottom + 22, fmt(value, value >= 10 ? 0 : 2), 11, "middle", "#5f6b77");
  }
  return svg;
}

function legend(series, x, y) {
  const height = series.length * 21 + 12;
  let svg = `<rect x="${x - 10}" y="${y - 12}" width="166" height="${height}" fill="#ffffff" stroke="#d9dee5"></rect>`;
  series.forEach((item, index) => {
    const yy = y + index * 21;
    const dash = item.dash ? ` stroke-dasharray="${item.dash}"` : "";
    svg += `<line x1="${x}" x2="${x + 22}" y1="${yy}" y2="${yy}" stroke="${item.color}" stroke-width="3"${dash}></line>`;
    svg += text(x + 30, yy + 4, item.name, 11, "start", "#374151");
  });
  return svg;
}

function svgStart(width, height) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" role="img"><rect width="${width}" height="${height}" fill="#ffffff"></rect>`;
}

function text(x, y, value, size = 12, anchor = "start", fill = "#111827") {
  return `<text x="${x.toFixed(1)}" y="${y.toFixed(1)}" font-family="Arial, Helvetica, sans-serif" font-size="${size}" fill="${fill}" text-anchor="${anchor}">${escapeHtml(String(value))}</text>`;
}

function systemPressure(fan, filter, airflowM3h, mediaAreaM2, loaded) {
  return fan.system_pressure_pa + filterPressure(filter, airflowM3h, mediaAreaM2, loaded);
}

function filterPressure(filter, airflowM3h, mediaAreaM2, loaded) {
  const velocity = airflowM3h / 3600 / Math.max(mediaAreaM2, 1e-9);
  const clean = filter.pressure_drop_ref_pa * Math.pow(velocity / filter.pressure_drop_ref_velocity_m_s, filter.pressure_drop_exponent);
  return clean * (loaded ? filter.loaded_pressure_drop_multiplier : 1);
}

function fanPressure(fan, airflowM3h) {
  if (!fan.free_airflow_m3h || !fan.shutoff_pressure_pa || airflowM3h >= fan.free_airflow_m3h) {
    return 0;
  }
  const ratio = Math.max(0, airflowM3h / fan.free_airflow_m3h);
  return fan.shutoff_pressure_pa * (1 - Math.pow(ratio, fan.curve_exponent));
}

function updateFanMode() {
  const mode = document.querySelector("input[name='fan-mode']:checked").value;
  document.querySelectorAll("[data-mode]").forEach((item) => {
    item.classList.toggle("hidden", item.dataset.mode !== mode);
  });
}

function updateFilterSizeMode() {
  const sizeMode = document.querySelector("input[name='filter-size-mode']:checked").value;
  const inputMode = document.querySelector("input[name='filter-input-mode']:checked").value;
  document.querySelectorAll("[data-filter-size-mode]").forEach((item) => {
    const sizeMatches = item.dataset.filterSizeMode === sizeMode;
    const inputMatches = !item.dataset.filterInputMode || item.dataset.filterInputMode === inputMode;
    item.classList.toggle("hidden", !sizeMatches || !inputMatches);
  });
  updateComputedMediaArea();
}

function updateComputedMediaArea() {
  const target = document.getElementById("computed-media-area");
  if (!target) {
    return;
  }
  const width = numberOrNull(document.querySelector("[data-path='filter.frontal_width_m']").value);
  const height = numberOrNull(document.querySelector("[data-path='filter.frontal_height_m']").value);
  const multiplier = numberOrNull(document.querySelector("[data-path='filter.pleat_area_multiplier']").value);
  if (!width || !height || !multiplier) {
    target.textContent = "N/A";
    return;
  }
  const frontalAreaMm2 = width * height;
  const mediaAreaMm2 = frontalAreaMm2 * multiplier;
  target.textContent = `${fmt(frontalAreaMm2, 0)} mm2 frontal x ${fmt(multiplier, 2)} = ${fmt(mediaAreaMm2, 0)} mm2 media`;
}

function applyFieldHelp() {
  tooltipElement = document.createElement("div");
  tooltipElement.className = "field-tooltip";
  tooltipElement.setAttribute("role", "tooltip");
  document.body.appendChild(tooltipElement);

  document.querySelectorAll("[data-path]").forEach((input) => {
    const help = fieldHelp[input.dataset.path];
    if (!help) {
      return;
    }
    const label = input.closest("label");
    if (!label) {
      return;
    }
    label.dataset.help = help;
    label.addEventListener("mouseenter", () => showFieldTooltip(label));
    label.addEventListener("mouseleave", hideFieldTooltip);
    label.addEventListener("focusin", () => showFieldTooltip(label));
    label.addEventListener("focusout", hideFieldTooltip);
  });
  window.addEventListener("scroll", hideFieldTooltip, true);
  window.addEventListener("resize", hideFieldTooltip);
}

function showFieldTooltip(label) {
  if (!tooltipElement || !label.dataset.help) {
    return;
  }
  tooltipElement.textContent = label.dataset.help;
  tooltipElement.classList.add("visible");
  tooltipElement.style.left = "0px";
  tooltipElement.style.top = "0px";

  const margin = 12;
  const gap = 8;
  const labelRect = label.getBoundingClientRect();
  const tooltipRect = tooltipElement.getBoundingClientRect();
  let left = labelRect.left;
  let top = labelRect.bottom + gap;

  if (left + tooltipRect.width > window.innerWidth - margin) {
    left = window.innerWidth - tooltipRect.width - margin;
  }
  if (left < margin) {
    left = margin;
  }
  if (top + tooltipRect.height > window.innerHeight - margin) {
    top = labelRect.top - tooltipRect.height - gap;
  }
  if (top < margin) {
    top = margin;
  }

  tooltipElement.style.left = `${left}px`;
  tooltipElement.style.top = `${top}px`;
}

function hideFieldTooltip() {
  if (tooltipElement) {
    tooltipElement.classList.remove("visible");
  }
}

function exportJson() {
  const data = {
    inputs: latestPayload || readForm(),
    result: latestResult
  };
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "pyfiltration-design.json";
  link.click();
  URL.revokeObjectURL(url);
}

function setStatus(message, isError = false) {
  const status = document.getElementById("status");
  status.textContent = message;
  status.classList.toggle("error", isError);
}

function getPath(object, path) {
  return path.split(".").reduce((current, key) => current && current[key], object);
}

function setPath(object, path, value) {
  const parts = path.split(".");
  let current = object;
  parts.slice(0, -1).forEach((part) => {
    current[part] = current[part] || {};
    current = current[part];
  });
  current[parts[parts.length - 1]] = value;
}

function numberOrNull(value) {
  if (value === "") {
    return null;
  }
  return Number(value);
}

function range(start, stop, steps) {
  const values = [];
  for (let i = 0; i <= steps; i += 1) {
    values.push(start + (stop - start) * i / steps);
  }
  return values;
}

function niceMax(value) {
  if (!Number.isFinite(value) || value <= 0) {
    return 1;
  }
  const exponent = Math.floor(Math.log10(value));
  const base = Math.pow(10, exponent);
  const scaled = value / base;
  if (scaled <= 1) return base;
  if (scaled <= 2) return 2 * base;
  if (scaled <= 5) return 5 * base;
  return 10 * base;
}

function fmt(value, digits = 1) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) {
    return "N/A";
  }
  return Number(value).toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits
  });
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }[char]));
}
