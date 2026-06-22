def test_import_main():
    import importlib

    main = importlib.import_module("main")
    assert hasattr(main, "parse_args")
