import json
import operator
import os
import time
import shutil
import logging

import subprocess

import six

LOG_FORMATTER = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
logger = logging.getLogger('archiver')

AUTO_ARCHIVE_FILES_CONFIG_DIR = '/etc/auto-archive-files'


class Entry(object):
    def __init__(self, entry):
        self.entry = entry
        self.path = entry.path
        self.name = entry.name

    @property
    def is_dir(self):
        return self.entry.is_dir()

    @property
    def is_symlink(self):
        return self.entry.is_symlink()

    @property
    def is_file(self):
        return self.entry.is_file()

    @property
    def mtime(self):
        return self.entry.stat().st_mtime

    @property
    def type(self):
        if self.is_dir:
            return 'dir'
        elif self.is_file:
            return 'file'
        elif self.is_symlink:
            return 'symlink'

    @property
    def msince(self):
        return time.time() - self.mtime

    def analize_filter(self, key, value):
        parts = key.split('__')
        field = getattr(self, parts.pop(0))
        if not parts:
            op = operator.eq
        else:
            op = getattr(operator, parts[0])
        return op(field, value)

    def filter(self, filters):
        for key, value in filters.items():
            if not self.analize_filter(key, value):
                return False
        return True

    def __repr__(self):
        return '<{} "{}">'.format((self.type or 'entry').title(), self.name)


def get_files(directory, filters=None):
    filters = filters or {}
    for entry in os.scandir(directory):
        entry = Entry(entry)
        if entry.is_symlink and not os.path.exists(entry.path):
            # Broken symlinks.
            continue
        if entry.is_dir:
            for subentry in get_files(entry.path, filters):
                yield subentry
        if entry.filter(filters):
            yield entry


def remove_empty_directories(path, root='/'):
    if path.rstrip('/') == root.rstrip('/') or os.listdir(path):
        return
    os.rmdir(path)
    remove_empty_directories(os.path.dirname(path), root)


class Archiver(object):
    def __init__(self, config):
        if isinstance(config, six.string_types):
            config = self.get_config(config)
        assert config is not None
        self.config = config
        self.log_to_file()

    def get_config(self, config_path):
        for candidate in [config_path, '{}/{}.json'.format(AUTO_ARCHIVE_FILES_CONFIG_DIR.rstrip('/'), config_path)]:
            if os.path.exists(candidate):
                return json.load(open(candidate))

    def log_to_file(self, file=None, logger_to_use=None):
        file = file or self.config['log_file']
        if not file:
            return
        logger_to_use = logger_to_use or logger
        fileHandler = logging.FileHandler(file)
        fileHandler.setFormatter(LOG_FORMATTER)
        logger_to_use.addHandler(fileHandler)

    def list(self):
        entries = get_files(self.config['src'], self.config['filters'])
        return list(filter(lambda x: x not in self.config['exclude'], entries))

    def on_fail_decorator(self, function):
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as e:
                body = 'Error on function {}.\nArgs: {}\nKwargs: {}\Exception: {}'.format(function, args, kwargs, e)
                if self.config.get('on_file'):
                    subject_body = ['[Auto Archive Files] FAILED to archive {}'.format(self.config['src']),
                                    body]
                    subprocess.Popen(self.config['on_fail'] + subject_body, env=self.config.get('env', {}))
                logger.error(body.replace('\n', '  '))
                return False
        return wrapper

    def archive(self):
        def remove(path):
            shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
        copy = self.on_fail_decorator(shutil.copy2 if self.config.get('copy_meta') else shutil.copyfile)
        remove = self.on_fail_decorator(remove)
        makedirs = self.on_fail_decorator(os.makedirs)
        rmdirs = self.on_fail_decorator(remove_empty_directories)
        for entry in self.list():
            src = entry.path
            relative_dst = entry.path.replace(self.config['src'], '').lstrip('/')
            dst = os.path.join(self.config['dst'], relative_dst)
            logger.info('Moving {} to {}'.format(src, dst))
            logger.debug('Creating {} directory if does not exists.'.format(os.path.dirname(dst)))
            makedirs(os.path.dirname(dst), exist_ok=True)
            logger.debug('Copying {} to {}'.format(src, dst))
            if copy(src, dst) is False:
                logger.error('Aborted for {} file on copy.'.format(src))
                continue
            else:
                logger.debug('{} has been copied successfully.'.format(src))
            logger.debug('Deleting {} in source'.format(src))
            if remove(src) is False:
                logger.error('It has not deleted the file {}'.format(src))
                continue
            else:
                logger.debug('{} has been removed successfully.'.format(src))
            logger.debug('Remove empty directories in {} directory.'.format(os.path.dirname(src)))
            rmdirs(os.path.dirname(src), self.config['src'])
