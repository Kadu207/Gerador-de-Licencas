"use client";

import { useState } from "react";
import { createClientAction } from "@/lib/actions/admin";

export function ClientForm({ parents }: { parents: { id: number; nome: string }[] }) {
  const [docType, setDocType] = useState<"cnpj" | "cpf">("cnpj");

  async function fetchCep(cep: string) {
    const digits = cep.replace(/\D/g, "");
    if (digits.length !== 8) return;
    const res = await fetch(`https://viacep.com.br/ws/${digits}/json/`);
    const data = await res.json();
    if (data.erro) return;
    (document.getElementById("logradouro") as HTMLInputElement).value = data.logradouro ?? "";
    (document.getElementById("bairro") as HTMLInputElement).value = data.bairro ?? "";
    (document.getElementById("cidade") as HTMLInputElement).value = data.localidade ?? "";
    (document.getElementById("uf") as HTMLInputElement).value = data.uf ?? "";
  }

  return (
    <form action={createClientAction} className="grid gap-4 md:grid-cols-2">
      <div>
        <label className="mb-1 block text-sm font-medium">Nome *</label>
        <input name="nome" required className="input-field" />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Razão social</label>
        <input name="razao_social" className="input-field" />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Tipo documento</label>
        <select
          name="document_type"
          className="input-field"
          value={docType}
          onChange={(e) => setDocType(e.target.value as "cnpj" | "cpf")}
        >
          <option value="cnpj">CNPJ</option>
          <option value="cpf">CPF</option>
        </select>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">{docType === "cnpj" ? "CNPJ" : "CPF"}</label>
        <input name={docType} className="input-field" placeholder={docType === "cnpj" ? "00.000.000/0000-00" : "000.000.000-00"} />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">E-mail 01</label>
        <input name="email" type="email" className="input-field" />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">E-mail 02</label>
        <input name="email_02" type="email" className="input-field" />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Telefone 01</label>
        <input name="telefone" className="input-field" />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Telefone 02</label>
        <input name="telefone_02" className="input-field" />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Telefone 03</label>
        <input name="telefone_03" className="input-field" />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Matriz (filial de)</label>
        <select name="parent_client_id" className="input-field" defaultValue="">
          <option value="">— Matriz —</option>
          {parents.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nome}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">ID clínica ERP (Cloud)</label>
        <input
          name="clinica_id_erp"
          type="number"
          min={1}
          className="input-field"
          placeholder="Opcional — vincula Excellence Dental Cloud"
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">ID clínica Lab</label>
        <input
          name="clinica_id_lab"
          type="number"
          min={1}
          className="input-field"
          placeholder="Opcional — vincula Dental Lab"
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">CEP</label>
        <input
          name="cep"
          id="cep"
          className="input-field"
          onBlur={(e) => fetchCep(e.target.value)}
          placeholder="00000-000"
        />
      </div>
      <div className="md:col-span-2">
        <label className="mb-1 block text-sm font-medium">Logradouro</label>
        <input name="logradouro" id="logradouro" className="input-field" />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Número</label>
        <input name="numero" className="input-field" />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Complemento</label>
        <input name="complemento" className="input-field" />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Bairro</label>
        <input name="bairro" id="bairro" className="input-field" />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Cidade</label>
        <input name="cidade" id="cidade" className="input-field" />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">UF</label>
        <input name="uf" id="uf" className="input-field" maxLength={2} />
      </div>
      <div className="md:col-span-2">
        <label className="mb-1 block text-sm font-medium">Observações</label>
        <textarea name="notes" className="input-field min-h-20" />
      </div>
      <div className="md:col-span-2">
        <button type="submit" className="btn btn-primary">
          Cadastrar cliente
        </button>
      </div>
    </form>
  );
}
