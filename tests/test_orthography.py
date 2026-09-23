from pauliceia.orthography import modernize


def test_cada_regra_de_digrafo():
    assert modernize("largo santa ephigenia")[0] == "largo santa efigenia"
    assert modernize("rua arthur motta")[0] == "rua artur mota"
    assert modernize("rua araguaya")[0] == "rua araguaia"
    assert modernize("rua bella cintra")[0] == "rua bela cintra"
    assert modernize("rua paulo affonso")[0] == "rua paulo afonso"
    assert modernize("viaducto santa ephigenia")[0] == "viaduto santa efigenia"


def test_aplica_multiplas_regras_e_registra_todas():
    modern, applied = modernize("viaducto santa ephigenia")
    assert modern == "viaduto santa efigenia"
    assert set(applied) == {"ct_to_t", "ph_to_f"}


def test_nome_sem_marcador_fica_intacto():
    modern, applied = modernize("rua carlos de campos")
    assert modern == "rua carlos de campos"
    assert applied == []


def test_nao_mexe_em_digrafos_legitimos_do_portugues():
    # 'lh' e 'nh' são fonemas próprios, e 'rr' e 'ss' intervocálicos continuam
    # válidos na ortografia moderna.
    assert modernize("rua carvalho")[0] == "rua carvalho"
    assert modernize("rua minhoca")[0] == "rua minhoca"
    assert modernize("alameda barros")[0] == "alameda barros"
    assert modernize("praça joao pessoa")[0] == "praça joao pessoa"
