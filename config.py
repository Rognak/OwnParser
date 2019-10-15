class Config:

    # prepocessing patterns
    pre_processing = [
        # delete scripts
        r'<(script).*?</\1>(?s)',
        # delete styles
        r'<(style).*?</\1>(?s)',
        # delete meta
        r'<(meta).*?>',
        # delete ul's (optional)
        '<(ul).*?</\1>(?s)',
        # delete navigation
        r'<(nav).*?</\1>(?s)',
        # delete footer
        r'<(footer).*?</\1>(?s)',
        # delete header
        r'<(header).*?</\1>(?s)',
        # delete forms
        r'<(form).*?</\1>(?s)'
    ]

    # cut strategy AVG or CUSTOM
    STRATEGY = "CUSTOM"

    # custom cut coefficient
    CUSTOM_COEFF = 0.5

    # forced <p> finding
    FORCED = True

    # MAX_LENGTH to formatter
    MAX_LENGTH = 80