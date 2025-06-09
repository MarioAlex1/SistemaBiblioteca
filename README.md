# Sistema de Biblioteca 📚

![Python](https://img.shields.io/badge/python-3.8+-blue)
![Flask](https://img.shields.io/badge/flask-v2.0-green)

## Descrição

Sistema web para gerenciamento de biblioteca desenvolvido em Python com Flask e SQLite. Permite cadastro e login de usuários (com permissão diferenciada para admin e alunos), cadastro de livros, empréstimos controlados e devoluções. Interface simples, funcional e segura.

## Tecnologias

- Python 3.8+
- Flask
- SQLite
- HTML/CSS (templates básicos)

## Funcionalidades

- Cadastro de usuários (somente admins podem cadastrar)
- Login e logout
- Cadastro, listagem e controle de livros
- Empréstimos com limite de 3 livros por usuário
- Controle de devoluções e disponibilidade de livros