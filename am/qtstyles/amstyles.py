def getStyleSheet(path):
    """
    read style sheet file for widgets
    """
    try:
        with open(path) as f:
            # f.open(QFile.ReadOnly | QFile.Text)
            stylesheet = f.read()
            # f.close()

            return stylesheet
    except Exception as e:
        print('   ... File {qss:s} has a problem\n      ... Error is {err!s}'.format(qss=path, err=e))
