#!/usr/bin/env python3
"""
Script de gerenciamento do banco de dados PostgreSQL para QuimioAnalytics
Autor: QuimioAnalytics Team
Data: 2026-04-26

Comandos disponíveis:
  - start: Inicia o container PostgreSQL
  - stop: Para o container
  - restart: Reinicia o container
  - logs: Exibe logs do container
  - status: Verifica status do container
  - init-schema: Inicializa o schema do banco
  - psql: Abre shell interativo do PostgreSQL
  - clean: Remove container e volumes (CUIDADO!)
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Configurações do banco
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'quimioanalytics',
    'user': 'quimio_user',
    'password': 'quimio_pass_2024'
}

CONTAINER_NAME = 'quimio_postgres'
PROJECT_ROOT = Path(__file__).parent.parent


def run_command(cmd, check=True, capture_output=False):
    """Executa comando no shell"""
    print(f"🔧 Executando: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        check=check,
        capture_output=capture_output,
        text=True
    )
    return result


def check_docker():
    """Verifica se Docker está instalado e rodando"""
    try:
        result = subprocess.run(
            ['docker', 'ps'],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker não está instalado ou não está rodando!")
        print("   Instale o Docker: https://docs.docker.com/get-docker/")
        return False


def container_exists():
    """Verifica se o container existe"""
    result = subprocess.run(
        ['docker', 'ps', '-a', '--filter', f'name={CONTAINER_NAME}', '--format', '{{.Names}}'],
        capture_output=True,
        text=True
    )
    return CONTAINER_NAME in result.stdout


def container_is_running():
    """Verifica se o container está rodando"""
    result = subprocess.run(
        ['docker', 'ps', '--filter', f'name={CONTAINER_NAME}', '--format', '{{.Names}}'],
        capture_output=True,
        text=True
    )
    return CONTAINER_NAME in result.stdout


def start_db():
    """Inicia o banco de dados usando docker-compose"""
    if not check_docker():
        return False
    
    print("🚀 Iniciando PostgreSQL no Docker...")
    os.chdir(PROJECT_ROOT)
    
    if container_is_running():
        print(f"✅ Container '{CONTAINER_NAME}' já está rodando!")
        return True
    
    run_command(['docker-compose', 'up', '-d'])
    
    print("⏳ Aguardando banco de dados ficar pronto...")
    time.sleep(5)
    
    # Aguarda health check
    for i in range(30):
        if container_is_running():
            result = subprocess.run(
                ['docker', 'exec', CONTAINER_NAME, 'pg_isready', 
                 '-U', DB_CONFIG['user'], '-d', DB_CONFIG['database']],
                capture_output=True
            )
            if result.returncode == 0:
                print("✅ Banco de dados está pronto!")
                print_connection_info()
                return True
        time.sleep(1)
    
    print("⚠️  Banco iniciado mas health check não confirmado")
    return True


def stop_db():
    """Para o banco de dados"""
    if not check_docker():
        return False
    
    print("🛑 Parando PostgreSQL...")
    os.chdir(PROJECT_ROOT)
    run_command(['docker-compose', 'stop'])
    print("✅ Container parado!")


def restart_db():
    """Reinicia o banco de dados"""
    print("🔄 Reiniciando PostgreSQL...")
    stop_db()
    time.sleep(2)
    start_db()


def show_logs():
    """Exibe logs do container"""
    if not check_docker():
        return False
    
    print("📋 Logs do PostgreSQL (Ctrl+C para sair):")
    os.chdir(PROJECT_ROOT)
    try:
        run_command(['docker-compose', 'logs', '-f', '--tail=100'])
    except KeyboardInterrupt:
        print("\n✅ Logs encerrados")


def show_status():
    """Exibe status do container"""
    if not check_docker():
        return False
    
    print("📊 Status do container:")
    run_command(['docker', 'ps', '-a', '--filter', f'name={CONTAINER_NAME}'])
    
    if container_is_running():
        print("\n✅ Container está RODANDO")
        print_connection_info()
    elif container_exists():
        print("\n⚠️  Container existe mas está PARADO")
        print("   Execute: python scripts/manage_db.py start")
    else:
        print("\n❌ Container NÃO EXISTE")
        print("   Execute: python scripts/manage_db.py start")


def init_schema():
    """Inicializa o schema do banco de dados"""
    if not container_is_running():
        print("❌ Container não está rodando. Inicie primeiro:")
        print("   python scripts/manage_db.py start")
        return False
    
    schema_file = PROJECT_ROOT / 'database' / 'schema_postgresql_mvp_entrega2.sql'
    if not schema_file.exists():
        print(f"❌ Arquivo de schema não encontrado: {schema_file}")
        return False
    
    print("🗄️  Inicializando schema do banco de dados...")
    
    cmd = [
        'docker', 'exec', '-i', CONTAINER_NAME,
        'psql', '-U', DB_CONFIG['user'], '-d', DB_CONFIG['database']
    ]
    
    with open(schema_file, 'r') as f:
        result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Schema criado com sucesso!")
        print("\n📊 Schemas disponíveis:")
        list_schemas()
    else:
        print("❌ Erro ao criar schema:")
        print(result.stderr)
        return False


def list_schemas():
    """Lista schemas disponíveis no banco"""
    cmd = [
        'docker', 'exec', CONTAINER_NAME,
        'psql', '-U', DB_CONFIG['user'], '-d', DB_CONFIG['database'],
        '-c', "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('core', 'stg', 'ref');"
    ]
    run_command(cmd, check=False)


def open_psql():
    """Abre shell interativo do PostgreSQL"""
    if not container_is_running():
        print("❌ Container não está rodando. Inicie primeiro:")
        print("   python scripts/manage_db.py start")
        return False
    
    print("🔌 Abrindo shell PostgreSQL (digite \\q para sair)...")
    cmd = [
        'docker', 'exec', '-it', CONTAINER_NAME,
        'psql', '-U', DB_CONFIG['user'], '-d', DB_CONFIG['database']
    ]
    subprocess.run(cmd)


def clean_db():
    """Remove container e volumes (CUIDADO!)"""
    print("⚠️  ATENÇÃO: Esta ação vai DELETAR TODOS OS DADOS!")
    response = input("   Digite 'sim' para confirmar: ")
    
    if response.lower() != 'sim':
        print("❌ Operação cancelada")
        return
    
    print("🗑️  Removendo container e volumes...")
    os.chdir(PROJECT_ROOT)
    run_command(['docker-compose', 'down', '-v'])
    print("✅ Container e volumes removidos!")


def print_connection_info():
    print("\n" + "=" * 60)
    print("INFORMACOES DE CONEXAO - DBeaver")
    print("=" * 60)
    print(f"Host:     {DB_CONFIG['host']}")
    print(f"Port:     {DB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"User:     {DB_CONFIG['user']}")
    print(f"Password: {os.getenv('DB_PASS', '***')}")
    print("=" * 60)
    print("\nPara conectar no DBeaver:")
    print("   1. Nova Conexao -> PostgreSQL")
    print("   2. Preencha os dados acima")
    print("   3. Test Connection -> OK -> Finish")
    print("=" * 60 + "\n")


def print_help():
    print("""
QuimioAnalytics - Gerenciador de Banco de Dados

Uso: python3 scripts/manage_db.py [comando]

COMANDOS DISPONIVEIS:
  start         Inicia o container PostgreSQL
  stop          Para o container
  restart       Reinicia o container
  status        Verifica status do container
  logs          Exibe logs do container (Ctrl+C para sair)
  init-schema   Cria schemas e tabelas no banco
  psql          Abre shell interativo do PostgreSQL
  clean         Remove container e volumes (ATENCAO: deleta dados!)
  help          Exibe esta ajuda

EXEMPLOS:
  python3 scripts/manage_db.py start
  python3 scripts/manage_db.py init-schema
  python3 scripts/manage_db.py status

WORKFLOW INICIAL:
  1. python3 scripts/manage_db.py start       # Inicia o banco
  2. python3 scripts/manage_db.py init-schema # Cria as tabelas
  3. Conectar no DBeaver com as credenciais exibidas
""")


def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    commands = {
        'start': start_db,
        'stop': stop_db,
        'restart': restart_db,
        'logs': show_logs,
        'status': show_status,
        'init-schema': init_schema,
        'psql': open_psql,
        'clean': clean_db,
        'help': print_help
    }
    
    if command not in commands:
        print(f"❌ Comando '{command}' não reconhecido!")
        print_help()
        sys.exit(1)
    
    commands[command]()


if __name__ == '__main__':
    main()
