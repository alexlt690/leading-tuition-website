def page_template(title, content):
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <link rel="stylesheet" href="style.css">
    </head>
    <body>
        <header>
            <h1>Leading Tuition</h1>
        </header>

        <main>
            <h2>{title}</h2>
            {content}
        </main>

        <footer>
            <p>Leading Tuition ©</p>
        </footer>
    </body>
    </html>
    """
