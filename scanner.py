"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
Symbol - encapsulates a symbol and stores its properties.
"""
import sys
from typing import List


class Symbol:

    """Encapsulate a symbol and store its properties.

    Parameters
    ----------
    No parameters.

    Public methods
    --------------
    No public methods.
    """

    def __init__(self):
        """Initialise symbol properties."""
        self.type = None
        self.id = None
        self.name = ""

    def __repr__(self) -> str:
        return f"Symbol(type={self.type}, id={self.id}, name={self.name})"


class SymbolList:
    def __init__(self):
        self.HEADING = "HEADING"
        self.LOGIC = "LOGIC"
        self.NUMBER = "NUMBER"
        self.NAME = "NAME"
        self.INPUT = "INPUT"
        self.OUTPUT = "OUTPUT"
        self.EQUAL = "EQUAL"
        self.DOT = "DOT"
        self.COMMA = "COMMA"
        self.SEMICOLON = "SEMICOLON"
        self.OPEN_BRACKET = "OPEN_BRACKET"
        self.CLOSE_BRACKET = "CLOSE_BRACKET"
        self.OPEN_SQUARE_BRACKET = "OPEN_SQUARE_BRACKET"
        self.CLOSE_SQUARE_BRACKET = "CLOSE_SQUARE_BRACKET"
        self.EOF = "EOF"


class ErrorCodes:
    INVALID_CHARACTER = "InvalidCharacter"
    INVALID_NAME = "InvalidName"
    INVALID_NUMBER = "InvalidNumber"

    description = {
        INVALID_CHARACTER: "This character is not allowed in the definition file.",
        INVALID_NAME: """
        The name used is either a reserved word or is not a valid name for a device.
        Names must start with a letter and can only contain letters, numbers. Logic gates symbols must be in upper case.
        """,
        INVALID_NUMBER: "Invalid number",
    }


class ScannerError(SyntaxError):

    """Exception raised for errors in the input.

    Attributes
    ----------
    message : str
        explanation of the error
    """

    def __init__(self, line_number, line_content, char_number, error_code, message):
        """Initialise ScannerError with the message."""
        self.error_code = error_code
        self.message = message
        self.line_number = line_number
        self.line_content = line_content
        self.char_number = char_number

        self.error_message = f"Error - {error_code}: {message}" + "\n" + \
            f"Line {self.line_number} Char {self.char_number}:\n{self.line_content}" + "\n" + \
            " " * (self.char_number) + "^" + "\n" + \
            "Description: " + ErrorCodes.description[error_code] + "\n"

    def __str__(self):
        return self.error_message

    def __repr__(self):
        return self.error_message


class Scanner(SymbolList):

    """Read circuit definition file and translate the characters into symbols.

    Once supplied with the path to a valid definition file, the scanner
    translates the sequence of characters in the definition file into symbols
    that the parser can use. It also skips over comments and irrelevant
    formatting characters, such as spaces and line breaks.

    Parameters
    ----------
    path: path to the circuit definition file.
    names: instance of the names.Names() class.

    Public methods
    -------------
    get_symbol(self): Translates the next sequence of characters into a symbol
                      and returns the symbol.
    """

    def __init__(self, path, names):
        """Open specified file and initialise reserved words and IDs."""
        SymbolList.__init__(self)
        try:
            self.file = open(path, "r")

        except FileNotFoundError:
            raise Exception("Input file not found")

        self.names = names
        self.errors: List[ScannerError] = []

        self.heading_list = ["devices", "conns", "monit"]

        self.logic_list = ["DTYPE", "NAND", "NOR",
                           "XOR", "AND", "OR", "CLOCK", "SWITCH"]

        # contact heading_list and logic_list all in lower case
        self.keywords = self.heading_list + self.logic_list
        self.keywords = [keyword.lower() for keyword in self.keywords]

        self.current_character = " "
        self.current_position = 0
        self.current_line = 0
        self.error_count = 0

    def get_all_symbols(self):
        """Return all symbols in the file."""
        symbols = []
        while True:
            symbol = self.get_symbol()
            symbols.append(symbol)
            if symbol.type == self.EOF:
                break
        return symbols

    def get_symbol(self):
        """Translate the next sequence of characters into a symbol."""
        self.skip_spaces()  # current character now not whitespace

        symbol = Symbol()

        if self.current_character == "#":  # Skip comments
            self.advance()
            while self.current_character != "\n":
                self.advance()

        self.skip_spaces()

        if self.current_character.isalpha():
            name_string = self.get_name()
            self.name_string = name_string[0]
            symbol.name = self.name_string

            if self.name_string in self.heading_list:
                symbol.type = self.HEADING
            elif self.name_string in self.logic_list:
                symbol.type = self.LOGIC
                [symbol.id] = self.names.lookup([self.name_string])
            else:
                symbol.type = self.NAME
                [symbol.id] = self.names.lookup([self.name_string])

                if symbol.name.lower() in self.keywords:
                    self.error_count += 1

                    error = ScannerError(
                        self.current_line, self.get_current_line(),
                        self.current_position - len(symbol.name),
                        ErrorCodes.INVALID_NAME,
                        f"Invalid name: {symbol.name}")

                    self.errors.append(error)

        elif self.current_character.isdigit():  # Numbers
            symbol.id = None
            symbol.name = self.get_number()[0]
            symbol.type = self.NUMBER

        elif self.current_character == "=":  # Definitions
            symbol.type = self.EQUAL
            symbol.name = "="
            self.advance()

        elif self.current_character == ".":  # Connections
            symbol.type = self.DOT
            symbol.name = "."
            self.advance()

        elif self.current_character == ",":  # Punctuations
            symbol.type = self.COMMA
            symbol.name = ","
            self.advance()

        elif self.current_character == ";":  # Punctuations
            symbol.type = self.SEMICOLON
            symbol.name = ";"
            self.advance()

        elif self.current_character == "(":  # Inputs No.
            symbol.type = self.OPEN_BRACKET
            symbol.name = "("
            self.advance()

        elif self.current_character == ")":  # Inputs No.
            symbol.type = self.CLOSE_BRACKET
            symbol.name = ")"
            self.advance()

        elif self.current_character == "[":  # Inputs No.
            symbol.type = self.OPEN_SQUARE_BRACKET
            symbol.name = "["
            self.advance()
        elif self.current_character == "]":  # Inputs No.
            symbol.type = self.CLOSE_SQUARE_BRACKET
            symbol.name = "]"
            self.advance()

        elif self.current_character == "":  # End of file
            symbol.name = "EOF"
            symbol.type = self.EOF

        else:  # Not a valid character
            error = ScannerError(self.current_line, self.current_character,
                                 self.current_position, ErrorCodes.INVALID_CHARACTER, "Invalid character")
            print(error)
            self.errors.append(error)
            self.error_count += 1

        return symbol

    def get_name(self):
        """Return the name and the next character that is non-alphanumeric"""
        # self.advance()
        name = ""
        self.skip_spaces()
        while self.current_character.isalnum():
            name += self.current_character
            self.advance()
        return [name, self.current_character]

    def get_number(self):
        """Return the numbers in the file and the next character"""
        number = ""
        while self.current_character.isdigit():
            number += self.current_character
            self.advance()
        return [int(number), self.current_character]

    def skip_spaces(self):
        """Skip all the spaces in the file"""
        while self.current_character.isspace():
            self.advance()

    def advance(self):
        """Advance to the next character in the file"""
        try:
            self.current_character = self.file.read(1)
        except FileNotFoundError:
            raise Exception("Input file not found")
        if self.current_character == "\n":  # End of line actions
            self.current_line += 1
            self.current_position = 0
        else:
            self.current_position += 1
        return self.current_character

    def get_current_line(self):
        """Return the current line from the file"""
        line = ""
        current_position = self.file.tell()
        self.file.seek(0)
        for _ in range(self.current_line + 1):
            line = self.file.readline()
        self.file.seek(current_position)
        return line
