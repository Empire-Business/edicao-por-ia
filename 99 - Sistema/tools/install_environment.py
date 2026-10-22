#!/usr/bin/env python3
"""Read-only installation inventory for the local AI. No downloads or app imports.

Works before the project's Python dependencies are installed. Commands are argv
arrays for the agent to inspect, never shell strings to evaluate automatically.
"""
import argparse
import json
import platform
import shutil
import sys
from pathlib import Path


def plan(root, system=None, machine=None, python_version=None, which=None, libc=None):
    root = Path(root).resolve()
    system = system or platform.system()
    machine = (machine or platform.machine()).lower()
    machine = {'amd64': 'x86_64', 'aarch64': 'arm64'}.get(machine, machine)
    version = tuple(python_version or sys.version_info[:2])
    which = which or shutil.which
    libc = platform.libc_ver()[0] if libc is None else libc
    managers = {'Darwin': ('brew',), 'Windows': ('winget',),
                'Linux': ('apt-get', 'dnf', 'pacman', 'zypper', 'apk')}.get(system, ())
    found = {name: which(name) for name in ('git', 'gh', 'ffmpeg', 'ffprobe', 'node', *managers)}
    target = system + '-' + machine
    voice_platform = target in ('Darwin-arm64', 'Windows-x86_64', 'Linux-x86_64')
    if system == 'Linux' and libc != 'glibc':
        voice_platform = False
    compatible_python = version in ((3, 11), (3, 12))
    actions = []
    if not compatible_python:
        actions.append('Preparar Python 3.12 lado a lado; reexecutar este diagnóstico com ele. Não substituir o Python do sistema.')
    if system not in ('Darwin', 'Windows', 'Linux'):
        actions.append('Sistema não reconhecido: consultar fontes oficiais antes de propor instalação; não executar comandos de outro sistema.')
    if not any(found.get(name) for name in managers):
        actions.append('Sem gerenciador encontrado: a IA deve obter instaladores oficiais e conferir arquitetura/assinatura; não entregar comandos ao leigo.')
    if not voice_platform:
        actions.append('Cortez Voz sem pacote aprovado para esta arquitetura/libc. Preparar as outras capacidades; investigar compatibilidade oficial sem trocar a origem ou ignorar hashes.')
    py = str(root / '.venv' / ('Scripts/python.exe' if system == 'Windows' else 'bin/python'))
    command = lambda *args: [py, str(root / 'factory.py'), *args]
    steps = [{'id': name, 'preview': command('dependencies', '--capability', name),
              'apply': command('dependencies', '--capability', name, '--apply')}
             for name in ('base', 'ffmpeg', 'speech', 'motion', 'studio-audio', 'audio-cleanup')]
    steps.append({'id': 'voice', 'performed_by': 'setup_apply',
                  'preview': command('dependencies', '--capability', 'voice')})
    return {'schema': 1, 'status': 'plan', 'read_only': True,
            'environment': {'system': system, 'architecture': machine, 'libc': libc if system == 'Linux' else None,
                            'python': '.'.join(map(str, version)), 'python_executable': sys.executable},
            'tools': found, 'package_managers': [name for name in managers if found.get(name)],
            'python_for_all_components': '3.12 (3.11 também aceito)',
            'compatible_python': compatible_python, 'voice_platform_supported': voice_platform,
            'speech_backend': 'mlx-whisper' if target == 'Darwin-arm64' else 'faster-whisper',
            'bootstrap': [sys.executable, '-m', 'venv', str(root / '.venv')] if compatible_python else None,
            'steps': steps,
            'setup_preview': command('setup', '--host', 'HOST_ESCOLHIDO', '--preserve-agent-config'),
            'setup_apply': command('setup', '--host', 'HOST_ESCOLHIDO', '--preserve-agent-config', '--apply'),
            'setup_requires_explicit_local_data_authorization': True,
            'check': command('doctor', '--smoke'), 'agent_actions': actions,
            'instructions': 'workflows/INSTALL_WITH_CLAUDE.md',
            'execution_order': 'bootstrap → dependências → setup autorizado → diagnóstico; substituir HOST_ESCOLHIDO por claude ou codex.',
            'limitations': 'Plano não comprova instalação, modelo baixado, banco iniciado ou fala gerada.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(plan(args.root), ensure_ascii=False, indent=2))
