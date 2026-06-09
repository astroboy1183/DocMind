def test_package_imports():
    import docmind

    assert docmind is not None


def test_config_loads():
    from docmind.config import settings

    assert settings.chunk_size > 0
    assert settings.retrieve_k >= settings.rerank_top_n
