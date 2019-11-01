from PyQt5.QtWidgets import QMessageBox

def get_continue_or_cancel(message="Processed will be cancelled!",
                           title="Title",
                           continue_button_text="Continue",
                           cancel_button_text="Cancel"):
    """Continue or cancel question, shown as a warning (i.e. more urgent than
       simple message)

       :param question: Question (string) asked
       :param title: Window title (string)
       :param continue_button_text: text to display on button
       :param cancel_button_text: text to display on button

       :return: True for "Continue", False for "Cancel"

       >>> import easygui_qt as easy
       >>> choice = easy.get_continue_or_cancel()

       .. image:: ../docs/images/get_continue_or_cancel.png
    """
    # print('get_continue_or_cancel: message is {:s}'.format(message))

    message_box = QMessageBox(QMessageBox.Warning, title, message, QMessageBox.NoButton)
    message_box.addButton(continue_button_text, QMessageBox.AcceptRole)
    message_box.addButton(cancel_button_text, QMessageBox.RejectRole)
    message_box.show()
    message_box.raise_()

    # display the message box
    reply = message_box.exec_()

    return reply == QMessageBox.AcceptRole


def getKeysByValues(dictOfElements, listOfValues):
    '''
    Get a list of keys from dictionary which has value that matches with any value in given list of values

    cfr: https://thispointer.com/python-how-to-find-keys-by-value-in-dictionary/
    '''
    listOfKeys = list()
    listOfItems = dictOfElements.items()
    for item  in listOfItems:
        if item[1] in listOfValues:
            listOfKeys.append(item[0])
    return listOfKeys
