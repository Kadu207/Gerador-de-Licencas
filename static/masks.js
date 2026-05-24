/** Máscaras de input — CPF, CNPJ, telefone, CEP */
(function () {
  function digitsOnly(v) { return (v || "").replace(/\D/g, ""); }

  function maskCpf(value) {
    const d = digitsOnly(value).slice(0, 11);
    return d
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
  }

  function maskCnpj(value) {
    const d = digitsOnly(value).slice(0, 14);
    return d
      .replace(/^(\d{2})(\d)/, "$1.$2")
      .replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/\.(\d{3})(\d)/, ".$1/$2")
      .replace(/(\d{4})(\d)/, "$1-$2");
  }

  function maskPhone(value) {
    const d = digitsOnly(value).slice(0, 11);
    if (d.length <= 10) {
      return d.replace(/(\d{2})(\d{4})(\d{0,4})/, "($1) $2-$3").trim();
    }
    return d.replace(/(\d{2})(\d{5})(\d{0,4})/, "($1) $2-$3").trim();
  }

  function maskCep(value) {
    const d = digitsOnly(value).slice(0, 8);
    return d.replace(/(\d{5})(\d)/, "$1-$2");
  }

  function applyMask(el, fn) {
    el.addEventListener("input", function () {
      const pos = el.selectionStart;
      el.value = fn(el.value);
      el.setSelectionRange(pos, pos);
    });
  }

  document.querySelectorAll("[data-mask=cpf]").forEach(function (el) { applyMask(el, maskCpf); });
  document.querySelectorAll("[data-mask=cnpj]").forEach(function (el) { applyMask(el, maskCnpj); });
  document.querySelectorAll("[data-mask=phone]").forEach(function (el) { applyMask(el, maskPhone); });
  document.querySelectorAll("[data-mask=cep]").forEach(function (el) { applyMask(el, maskCep); });

  const docType = document.getElementById("document_type");
  const docField = document.getElementById("document_field");
  if (docType && docField) {
    function updateDocMask() {
      const isCpf = docType.value === "cpf";
      docField.name = isCpf ? "cpf" : "cnpj";
      docField.placeholder = isCpf ? "000.000.000-00" : "00.000.000/0000-00";
      docField.setAttribute("data-mask", isCpf ? "cpf" : "cnpj");
      docField.value = "";
    }
    docType.addEventListener("change", updateDocMask);
    updateDocMask();
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
        const set = function (id, val) {
          const el = document.getElementById(id);
          if (el) el.value = val || "";
        };
        set("logradouro", data.logradouro);
        set("bairro", data.bairro);
        set("cidade", data.cidade);
        set("uf", data.uf);
      } catch (_) {}
    });
  }

  const cnpjLookup = document.getElementById("cnpj_lookup");
  if (cnpjLookup) {
    cnpjLookup.addEventListener("click", async function () {
      const field = document.querySelector("[name=cnpj]");
      if (!field) return;
      const cnpj = digitsOnly(field.value);
      if (cnpj.length !== 14) return;
      try {
        const res = await fetch("/api/cnpj/" + cnpj);
        if (!res.ok) return;
        const data = await res.json();
        const set = function (name, val) {
          const el = document.querySelector("[name=" + name + "]");
          if (el) el.value = val || "";
        };
        set("razao_social", data.razao_social);
        set("nome", data.nome_fantasia || data.razao_social);
      } catch (_) {}
    });
  }
})();
