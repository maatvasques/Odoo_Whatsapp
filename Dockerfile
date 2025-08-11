# Usamos a imagem oficial do Odoo 17 como base
FROM odoo:17.0

# Trocamos para o usuário root para poder instalar pacotes
USER root

# Instala as dependências Python listadas no requirements.txt
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Retorna para o usuário padrão do Odoo por segurança
USER odoo