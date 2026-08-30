from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from .certificate import Certificate
from .event import Event
import re
import unicodedata
import logging

import random
import string

# Configure logger for this module
logger = logging.getLogger(__name__)


class Participant(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    validation_code: Optional[str] = Field(
        default_factory=lambda: "".join(random.choices(string.hexdigits, k=9)),
        init=False,
    )
    certificate: Optional[Certificate] = None
    event: Optional[Event] = None
    authenticity_verification_url: Optional[str] = None

    def __str__(self):
        return f"Participant: {self.first_name} {self.last_name} - {self.email}"

    # criar metodo name_completed
    def name_completed(self):
        self.first_name = self.first_name.lower()
        self.last_name = self.last_name.lower()

        name_completed = self.first_name + " " + self.last_name
        if len(name_completed.split(" ")) > 3:
            self.first_name = name_completed.split()[0]
            self.last_name = (
                name_completed.split()[1] + " " + name_completed.split()[-1]
            )
            name_completed = self.first_name + " " + self.last_name

        return name_completed.title()

    def _sanitize_filename(self, text: str) -> str:
        """
        Sanitiza uma string para ser usada como nome de arquivo no S3.
        Remove ou substitui caracteres especiais que podem causar problemas em URLs.

        Args:
            text (str): Texto a ser sanitizado

        Returns:
            str: Texto sanitizado adequado para nomes de arquivo S3
        """
        # Normaliza caracteres unicode (remove acentos)
        text = unicodedata.normalize("NFD", text)
        text = "".join(char for char in text if unicodedata.category(char) != "Mn")

        # Substitui caracteres especiais comuns por versões seguras
        special_chars = {
            "º": "o",
            "ª": "a",
            "×": "x",
            "@": "_at_",
            "&": "_and_",
            "+": "_plus_",
            "=": "_equals_",
            "%": "_percent_",
            "#": "_hash_",
            "?": "_question_",
            "/": "_slash_",
            "\\": "_backslash_",
            ":": "_colon_",
            ";": "_semicolon_",
            "<": "_lt_",
            ">": "_gt_",
            "|": "_pipe_",
            "*": "_star_",
            '"': "_quote_",
            "'": "_apostrophe_",
        }

        # Aplica as substituições de caracteres especiais
        for char, replacement in special_chars.items():
            text = text.replace(char, replacement)

        # Remove caracteres que não são alfanuméricos, espaços, hífens ou underscores
        text = re.sub(r"[^\w\s\-_]", "", text)

        # Substitui espaços múltiplos por um único espaço
        text = re.sub(r"\s+", " ", text)

        # Substitui espaços por underscores
        text = text.replace(" ", "_")

        # Remove underscores múltiplos consecutivos
        text = re.sub(r"_+", "_", text)

        # Remove underscores do início e fim
        text = text.strip("_")

        return text

    def formated_validation_code(self):
        self.validation_code = self.validation_code.upper()
        return f"{self.validation_code[0:3]}-{self.validation_code[3:6]}-{self.validation_code[6:9]}"

    def create_name_certificate(self):
        # Sanitiza o nome do participante e o nome do produto separadamente
        sanitized_name = self._sanitize_filename(self.name_completed())
        sanitized_product = self._sanitize_filename(self.event.product_name)
        sanitized_validation = self._sanitize_filename(self.formated_validation_code())

        # Combina os componentes sanitizados
        name_certificate = (
            f"{sanitized_name}{sanitized_product}_{sanitized_validation}.png"
        )

        logger.info(
            f"Nome do participante antes da sanitização: {self.name_completed()}"
        )
        logger.info(f"Nome do produto antes da sanitização: {self.event.product_name}")
        logger.info(
            f"Código de validação antes da sanitização: {self.formated_validation_code()}"
        )
        logger.info(f"Nome do certificado após a sanitização: {name_certificate}")

        return name_certificate
