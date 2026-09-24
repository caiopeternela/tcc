from pauliceia.clean import clean_name, normalize_group, rejection_reason


def _clean_and_judge(name):
    cleaned = clean_name(name)
    return cleaned, rejection_reason(cleaned)


def test_aceita_registro_bom():
    assert _clean_and_judge("rua bella cintra") == ("rua bella cintra", None)


def test_rejeita_nome_vazio():
    assert rejection_reason(clean_name("")) == "nome_vazio"
    assert rejection_reason(clean_name("   ")) == "nome_vazio"


def test_rejeita_placeholder_n_o():
    assert rejection_reason("n.o") == "placeholder"


def test_placeholder_no_fim_rejeita_o_registro():
    assert _clean_and_judge("rua 1 (n.o)")[1] == "placeholder"


def test_aceita_nome_com_palavra_no_legitima():
    assert rejection_reason("rua no convento") is None


def test_nao_oficial_so_casa_o_nome_inteiro():
    assert rejection_reason("rua oficial") is None
    assert rejection_reason("rua das officinas") is None
    assert rejection_reason("rua nao oficial de baixo") is None


def test_marcador_na_e_removido_mas_nome_e_mantido():
    assert _clean_and_judge("rua leocadia cintra (n.a)") == ("rua leocadia cintra", None)


def test_marcador_na_sozinho_e_rejeitado_como_vazio():
    assert _clean_and_judge("(n.a)") == ("", "nome_vazio")


def test_sufixo_de_lado_e_removido():
    assert _clean_and_judge("largo coracao de jesus impar") == ("largo coracao de jesus", None)
    assert _clean_and_judge("largo coracao de jesus par") == ("largo coracao de jesus", None)


def test_anotacao_atual_sai_do_nome_indexavel():
    # no dado real a anotação vem antes do sufixo de lado, então o sufixo tem de
    # sair primeiro para expor a anotação no fim da string.
    for raw in ("largo do riachuelo (atual praca da bandeira)", "largo do riachuelo (atual praca da bandeira) impar"):
        assert clean_name(raw) == "largo do riachuelo"


def test_rua_par_e_rua_impar_ficam_intactos():
    assert _clean_and_judge("rua par") == ("rua par", None)
    assert _clean_and_judge("rua impar") == ("rua impar", None)


def test_normaliza_grupo_colapsando_espacos():
    assert normalize_group("rua   bella  cintra ") == "rua bella cintra"


def test_grupo_e_o_mesmo_para_segmentos_da_mesma_via():
    assert normalize_group("avenida tamanduatehy") == normalize_group("avenida tamanduatehy ")
