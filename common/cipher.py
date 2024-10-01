#!/usr/bin/env python
#
# Copyright (c) 2023 Diego L. Pedro <diegolpedro@gmail.com>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Archivo de codificacion
#
from getpass import getpass
from cryptography.fernet import Fernet
import subprocess
import sys


if __name__ == '__main__':

    try:
        with open(".pgpass", "rb") as file:
            # Desencriptar
            linea = file.read()
            key = linea.split(b'\n')[0]
            enc_passwd = linea.split(b'\n')[1]
            cipher_suite = Fernet(key)
            passwd = cipher_suite.decrypt(enc_passwd).decode('utf-8')

            # Genera archivo .env 
            if len(sys.argv) > 1 and sys.argv[1] == '-g':
                with open("db.env", "a+") as filew:
                    filew.write("PGUSER=dbUser\nPGPASS="
                                + passwd + "\nPGDB=portfolio_db")
                filew.close()

        file.close()

    except FileNotFoundError:
        # Encriptar
        passwd = getpass("Ingrese password de la base: ")
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        enc_passwd = cipher_suite.encrypt(passwd.encode('utf-8'))
        with open(".pgpass", "wb") as file:
            file.write(key + b'\n')
            file.write(enc_passwd + b'\n')

        # passwd = getpass("Ingrese password de la API: ")              # Momentaneamente sin uso
        # enc_passwd = cipher_suite.encrypt(passwd.encode('utf-8'))     #
        # with open(".apipass", "wb") as file:                          #
        #     file.write(enc_passwd)                                    #

        subprocess.Popen(f'chmod 600 .pgpass', shell=True).wait()
        # subprocess.Popen(f'chmod 600 .apipass', shell=True).wait()    # Momentaneamente sin uso
