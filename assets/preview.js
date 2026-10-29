// MermaidPreview page logic: render the diagram, then zoom, pan and fit by transforming
// #stage only. The rendered SVG is never modified after it is inserted.
(function () {
  "use strict";

  var MIN_SCALE = 0.05;
  var MAX_SCALE = 20;
  var FIT_MARGIN = 24;

  var data = window.MERMAID_PREVIEW;
  var viewport = document.getElementById("viewport");
  var stage = document.getElementById("stage");
  var zoomLabel = document.getElementById("zoom");
  var LINE_HEIGHT = 16; // pixels per wheel "line", for mice that report deltaMode 1
  var view = { x: 0, y: 0, scale: 1 };
  var size = { width: 0, height: 0 };
  var fitted = false; // true until the user zooms or pans; then resize keeps their view

  function showError(message) {
    document.body.textContent = "";
    var p = document.createElement("p");
    p.className = "error";
    p.textContent = "Mermaid render error: " + message;
    var pre = document.createElement("pre");
    pre.textContent = data.source;
    document.body.appendChild(p);
    document.body.appendChild(pre);
  }

  function apply() {
    stage.style.transform =
      "translate(" + view.x + "px, " + view.y + "px) scale(" + view.scale + ")";
    zoomLabel.textContent = Math.round(view.scale * 100) + "%";
  }

  function clamp(scale) {
    return Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale));
  }

  function fit() {
    fitted = true;
    if (!(size.width > 0 && size.height > 0)) {
      // An empty or unmeasurable diagram: show it at 100% instead of dividing by zero.
      view.scale = 1;
      view.x = FIT_MARGIN;
      view.y = FIT_MARGIN;
      apply();
      return;
    }
    var w = Math.max(1, viewport.clientWidth - 2 * FIT_MARGIN);
    var h = Math.max(1, viewport.clientHeight - 2 * FIT_MARGIN);
    view.scale = clamp(Math.min(w / size.width, h / size.height));
    view.x = (viewport.clientWidth - size.width * view.scale) / 2;
    view.y = (viewport.clientHeight - size.height * view.scale) / 2;
    apply();
  }

  // Zoom by `factor`, keeping the diagram point under (px, py) fixed on screen.
  function zoomAt(px, py, factor) {
    var next = clamp(view.scale * factor);
    var ratio = next / view.scale;
    view.x = px - (px - view.x) * ratio;
    view.y = py - (py - view.y) * ratio;
    view.scale = next;
    fitted = false;
    apply();
  }

  function sizeSvg(svg) {
    var box = svg.viewBox && svg.viewBox.baseVal;
    var rect = svg.getBoundingClientRect();
    size.width = box && box.width ? box.width : rect.width;
    size.height = box && box.height ? box.height : rect.height;
    svg.style.maxWidth = "none";
    svg.setAttribute("width", size.width);
    svg.setAttribute("height", size.height);
  }

  function bindControls() {
    viewport.addEventListener("wheel", function (e) {
      e.preventDefault();
      var r = viewport.getBoundingClientRect();
      // deltaY is in pixels, lines or pages, depending on the device (deltaMode 0, 1, 2).
      var dy = e.deltaY;
      if (e.deltaMode === 1) dy *= LINE_HEIGHT;
      else if (e.deltaMode === 2) dy *= viewport.clientHeight;
      // Trackpad pinch arrives as a wheel event with ctrlKey set; it needs a stronger factor.
      var factor = Math.exp(-dy * (e.ctrlKey ? 0.01 : 0.0015));
      zoomAt(e.clientX - r.left, e.clientY - r.top, factor);
    }, { passive: false });

    var drag = null;
    viewport.addEventListener("pointerdown", function (e) {
      if (e.button !== 0) return;
      drag = { id: e.pointerId, x: e.clientX, y: e.clientY };
      viewport.setPointerCapture(e.pointerId);
      viewport.classList.add("dragging");
    });
    viewport.addEventListener("pointermove", function (e) {
      if (!drag || e.pointerId !== drag.id) return;
      view.x += e.clientX - drag.x;
      view.y += e.clientY - drag.y;
      drag.x = e.clientX;
      drag.y = e.clientY;
      fitted = false;
      apply();
    });
    function endDrag(e) {
      if (!drag || e.pointerId !== drag.id) return;
      drag = null;
      viewport.classList.remove("dragging");
    }
    viewport.addEventListener("pointerup", endDrag);
    viewport.addEventListener("pointercancel", endDrag);
    // The browser can take the pointer away without pointerup (for example on a window switch).
    viewport.addEventListener("lostpointercapture", endDrag);

    document.getElementById("fit").addEventListener("click", fit);
    document.addEventListener("keydown", function (e) {
      if (e.key === "0" && !e.metaKey && !e.ctrlKey && !e.altKey) fit();
    });
    window.addEventListener("resize", function () {
      if (fitted) fit();
    });
  }

  function start() {
    var config = Object.assign({}, data.config, { startOnLoad: false });
    try {
      mermaid.initialize(config);
    } catch (err) {
      showError(err && err.message ? err.message : String(err));
      return;
    }
    mermaid.render("mermaid-preview-svg", data.source).then(function (result) {
      stage.innerHTML = result.svg; // Mermaid's own output, rendered locally from the source.
      if (result.bindFunctions) result.bindFunctions(stage);
      sizeSvg(stage.querySelector("svg"));
      bindControls();
      fit();
      document.body.setAttribute("data-rendered", "true");
    }).catch(function (err) {
      showError(err && err.message ? err.message : String(err));
    });
  }

  start();
})();
