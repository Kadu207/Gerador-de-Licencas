/** Máscaras CPF/CNPJ/telefone/CEP + consulta RF automática */
(function () {
  function digitsOnly(v) {
    return (v || "").replace(/\D/g, "");
  }

  function maskCpf(value) {
    const d = digitsOnly(value).slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
    if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  }

  function maskCnpj(value) {
    const d = digitsOnly(value).slice(0, 14);
    if (d.length <= 2) return d;
    if (d.length <= 5) return d.slice(0, 2) + "." + d.slice(2);
    if (d.length <= 8) return d.slice(0, 2) + "." + d.slice(2, 5) + "." + d.slice(5);
    if (d.length <= 12) return d.slice(0, 2) + "." + d.slice(2, 5) + "." + d.slice(5, 8) + "/" + d.slice(8);
    return d.slice(0, 2) + "." + d.slice(2, 5) + "." + d.slice(5, 8) + "/" + d.slice(8, 12) + "-" + d.slice(12);
  }

  /** Fixo 10 dígitos: (XX) XXXX-XXXX | Celular 11: (XX) XXXXX-XXXX */
  function maskPhone(value) {
    const d = digitsOnly(value).slice(0, 11);
    const len = d.length;
    if (len === 0) return "";
    if (len <= 2) return "(" + d;
    if (len <= 6) return "(" + d.slice(0, 2) + ") " + d.slice(2);
    if (len <= 10) {
      return "(" + d.slice(0, 2) + ") " + d.slice(2, 6) + "-" + d.slice(6);
    }
    return "(" + d.slice(0, 2) + ") " + d.slice(2, 7) + "-" + d.slice(7);
  }

  function maskCep(value) {
    const d = digitsOnly(value).slice(0, 8);
    if (d.length <= 5) return d;
    return d.slice(0, 5) + "-" + d.slice(5);
  }

  const MASKS = { cpf: maskCpf, cnpj: maskCnpj, phone: maskPhone, cep: maskCep };

  function caretAfterDigits(formatted, digitCount) {
    if (digitCount <= 0) return 0;
    let seen = 0;
    for (let i = 0; i < formatted.length; i++) {
      if (/\d/.test(formatted[i])) {
        seen++;
        if (seen >= digitCount) return i + 1;
      }
    }
    return formatted.length;
  }

  function applyMask(el, fn) {
    const raw = el.value;
    const start = el.selectionStart ?? raw.length;
    const end = el.selectionEnd ?? start;
    const digitsBefore = digitsOnly(raw.slice(0, start)).length;
    const masked = fn(raw);
    el.value = masked;
    const next = caretAfterDigits(masked, digitsBefore);
    try {
      el.setSelectionRange(next, next);
    } catch (_) {}
  }

  function bindMask(el, fn) {
    if (!el || el.dataset.maskBound === "1") return;
    el.dataset.maskBound = "1";

    if (el.value) {
      el.value = fn(el.value);
    }

    el.addEventListener("input", function () {
      applyMask(el, fn);
    });

    el.addEventListener("paste", function () {
      requestAnimationFrame(function () {
        applyMask(el, fn);
      });
    });
  }

  function bindAllMasks(root) {
    (root || document).querySelectorAll("[data-mask]").forEach(function (el) {
      const kind = el.getAttribute("data-mask");
      if (MASKS[kind]) bindMask(el, MASKS[kind]);
    });
  }

  function setField(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val || "";
  }

  function showDocHint(msg, isError) {
    const hint = document.getElementById("doc_hint");
    if (!hint) return;
    hint.textContent = msg || "";
    hint.className = isError ? "field-hint error" : "field-hint";
  }

  async function lookupCnpj(cnpj) {
    const res = await fetch("/api/cnpj/" + cnpj);
    if (!res.ok) {
      const err = await res.json().catch(function () { return {}; });
      throw new Error(err.detail || "CNPJ não encontrado na Receita Federal");
    }
    return res.json();
  }

  async function autoLookupCnpjIfReady() {
    const docType = document.getElementById("document_type");
    const docField = document.getElementById("document_field");
    if (!docField || !docType || docType.value !== "cnpj") return;
    const cnpj = digitsOnly(docField.value);
    if (cnpj.length !== 14) return;
    showDocHint("Consultando Receita Federal…", false);
    try {
      const data = await lookupCnpj(cnpj);
      setField("razao_social", data.razao_social);
      const nome = document.querySelector("[name=nome]");
      if (nome && !nome.value.trim()) {
        nome.value = data.nome_fantasia || data.razao_social || "";
      }
      showDocHint("Dados da Receita Federal preenchidos automaticamente.", false);
    } catch (e) {
      showDocHint(e.message || "Falha na consulta RF", true);
    }
  }

  const docType = document.getElementById("document_type");
  const docField = document.getElementById("document_field");
  if (docType && docField) {
    function updateDocMask() {
      const isCpf = docType.value === "cpf";
      docField.name = isCpf ? "cpf" : "cnpj";
      docField.placeholder = isCpf ? "000.000.000-00" : "00.000.000/0000-00";
      docField.setAttribute("data-mask", isCpf ? "cpf" : "cnpj");
      docField.dataset.maskBound = "0";
      docField.value = "";
      showDocHint("", false);
      bindMask(docField, isCpf ? maskCpf : maskCnpj);
    }
    docType.addEventListener("change", updateDocMask);
    updateDocMask();

    docField.addEventListener("blur", autoLookupCnpjIfReady);
    docField.addEventListener("input", function () {
      const isCnpj = docType.value === "cnpj";
      if (isCnpj && digitsOnly(docField.value).length === 14) {
        autoLookupCnpjIfReady();
      }
    });
  }

  bindAllMasks(document);

  const clientModal = document.getElementById("client-modal");
  if (clientModal) {
    clientModal.addEventListener("close", function () {
      clientModal.querySelectorAll("input[data-mask]").forEach(function (el) {
        el.value = "";
      });
    });
  }

  const cepInput = document.getElementById("cep");
  if (cepInput) {
    cepInput.addEventListener("blur", async function () {
      const cep = digitsOnly(cepInput.value);
      if (cep.length !== 8) return;
      try {
        const res = await fetch("/api/cep/" + cep);
        if (!res.ok) return;
        const data = await res.json();
        setField("logradouro", data.logradouro);
        setField("bairro", data.bairro);
        setField("cidade", data.cidade);
        setField("uf", data.uf);
      } catch (_) {}
    });
  }
})();
