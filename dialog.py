#!/usr/bin/env python2.7
'''
Interactive dialog to select file(s).
Created on 29 Jun 2015

:author: yaswant.pradhan
:copyright: Crown copyright. Met Office
'''

import os.path as path
import Tkinter

def pickfile(initialdir=None, filetype=[('All types', '*')]):
    """
    Single file selector dialog.

    Kwargs:
     * initialdir (str): initial directory to select files
     * filetype (list): list of tuples in ('file type', 'file extension') format

    Returns:
     * Selected filename

    Raises:
     * SystemExit: When nothing selected from the dialog box.
    """

    from tkFileDialog import askopenfilename

    # remove the empty application window that pops up behind the file dialogs
    Tkinter.Tk().withdraw()

    # set initial directory (OS independent)
    home = path.expanduser("~")
    if not initialdir: initialdir = home
    if initialdir and not path.exists(initialdir):
        print "** {0} doesnot exist. Please select a valid path **".\
            format(initialdir)
        initialdir = home

    fi = askopenfilename(initialdir=initialdir,
                            filetypes=filetype,
                            title='Pick file(s)')
    if not fi: raise SystemExit("Oops!  No file was picked.")
    return fi


def pickfiles(initialdir=None, filetype=[('All types', '*')]):
    """
    Multiple file selector dialog.

    Kwargs:
     * initialdir (str): initial directory to select files
     * filetype (list): list of tuples in ('file type', 'file extension') format

    Returns:
     * Selected filenames (tuple)

    Raises:
     * SystemExit: When nothing selected from the dialog box.
    """

    from tkFileDialog import askopenfilenames

    # remove the empty application window that pops up behind the file dialogs
    Tkinter.Tk().withdraw()

    # set initial directory (OS independent)
    home = path.expanduser("~")
    if not initialdir: initialdir = home
    if initialdir and not path.exists(initialdir):
        print "** {0} doesnot exist. Please select a valid path **".\
            format(initialdir)
        initialdir = home
    files = askopenfilenames(initialdir=initialdir,
                            filetypes=filetype,
                            title='Pick file(s)')
    if not files: raise SystemExit("Oops!  No file was picked.")
    return files


if __name__ == '__main__':
    pass
