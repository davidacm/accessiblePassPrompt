# version 0.2.

* Fixed the message when the password has been typed. This use core.callLater. It was tested with strings of 700 characters, and the announcement works properly.
* Added the script to show the dialog to the "system focus" category.
* Now the validation to open the dialog is by checking the role of the focus object. If the role is "EDITABLETEXT", the dialog will be shown.
* Now the dialog is closed if the user press the command to open it when the dialog is already opened. It can be useful if the user doesn't know where is the dialog window.
* Updated documentation.

# version 0.1.

The first version of this add-on
