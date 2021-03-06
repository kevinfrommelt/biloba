"""
Tests for `biloba.config`.
"""

import unittest

from biloba import config


class ParseAddressTestCase(unittest.TestCase):
    """
    Tests for `config.parse_address`
    """

    def test_address(self):
        """
        Ensure that is basically works
        """
        host, port = config.parse_address('foo:1234')

        self.assertEqual(host, 'foo')
        self.assertEqual(port, 1234)

    def test_no_port(self):
        host, port = config.parse_address('foo')

        self.assertEqual(host, 'foo')
        self.assertIsNone(port)

    def test_port_is_not_int(self):
        with self.assertRaises(ValueError):
            config.parse_address('foo:bar')


class GetKeyTestCase(unittest.TestCase):
    """
    Tests for `config.get_key`
    """

    config = {
        'foo': {
            'bar': [1, 2, 3],
        },
        1: 'bar'
    }

    def test_missing_key(self):
        """
        Ensure that the default is returned when the key is missing from the
        config
        """
        with self.assertRaises(KeyError):
            config.get_key(self.config, 'bar')

        missing = object()

        ret = config.get_key(self.config, 'bar', missing)

        self.assertIs(ret, missing)

    def test_not_dotted(self):
        """
        A key on the first layer returns the correct value
        """
        self.assertEqual(
            config.get_key(self.config, 'foo'),
            self.config['foo']
        )

    def test_dotted(self):
        """
        dotted notation must be supported.
        """
        self.assertEqual(
            config.get_key(self.config, 'foo.bar'),
            self.config['foo']['bar']
        )

    def test_int(self):
        """
        An non string key should still work.
        """
        self.assertEqual(
            config.get_key(self.config, 1),
            'bar'
        )


class ConfigTestCase(unittest.TestCase):
    """
    Tests for `config.Config`
    """

    my_config = {
        'http': {
            'address': '127.0.0.1',
            'port': 4000,
        },
        'logger': {
            'address': '${http.address}',
        }
    }

    def test_sanity(self):
        conf = config.Config(self.my_config)

        self.assertEqual(
            conf.get('logger.address'),
            '127.0.0.1'
        )

    def test_expand_list(self):
        my_config = {
            'foo': {
                'a': 'A',
                'b': 'B',
            },
            'bar': ['${foo.a}', 1, '${foo.b}']
        }

        conf = config.Config(my_config)

        self.assertEqual(
            conf['bar'],
            ['A', 1, 'B'],
        )

    def test_expand_dict(self):
        my_config = {
            'foo': {
                'a': 'A',
                'b': 'B',
            },
            'bar': {
                'c': '${foo.a}',
                'd': '${foo.b}'
            },
        }

        conf = config.Config(my_config)

        self.assertEqual(
            conf['bar'],
            dict(c='A', d='B'),
        )

    def test_setdefault(self):
        a = object()
        b = object()

        conf = config.Config()

        conf.setdefault('a', a)
        self.assertIs(conf['a'], a)
        conf.setdefault('a', b)
        self.assertIs(conf['a'], a)

    def test_missing(self):
        """
        A missing key must raise `KeyError`.
        """
        conf = config.Config()

        with self.assertRaises(KeyError):
            conf['foobar']

    def test_set(self):
        """
        Just like a dict, a key must be able to be `set`.
        """
        conf = config.Config()

        conf['foo'] = 'bar'

        self.assertEqual(conf['foo'], 'bar')

    def test_set_dotted(self):
        """
        Set nested values using dot notation.
        """
        conf = config.Config()

        conf['foo'] = {}
        conf['foo.bar'] = 'baz'

        self.assertEqual(conf['foo.bar'], 'baz')
        self.assertEqual(conf['foo']['bar'], 'baz')

    def test_set_dotted_multiple(self):
        """
        Set nested values using dot notation (multiple dots).
        """
        conf = config.Config()

        conf['foo'] = {'bar': {}}
        conf['foo.bar.baz'] = 'pies'

        self.assertEqual(conf['foo.bar.baz'], 'pies')
        self.assertEqual(conf['foo']['bar']['baz'], 'pies')

    def test_set_dotted_missing_key(self):
        """
        A missing key in the dot notation path must raise a `KeyError`.
        """
        conf = config.Config()

        conf['foo'] = {}

        with self.assertRaises(KeyError):
            conf['foo.bar.baz'] = 'pies'

    def test_set_dotted_non_dict(self):
        """
        Setting a value on an object that doesn't implement `__setitem__` must
        raise a `TypeError`.
        """
        conf = config.Config()

        conf['foo'] = {'bar': 'baz'}

        with self.assertRaises(TypeError):
            conf['foo.bar.baz'] = 'pies'

    def test_contains(self):
        """
        Just like a dict, __contains__ should work as expected.
        """
        conf = config.Config()

        conf['foo'] = 'bar'

        self.assertNotIn('bar', conf)
        self.assertIn('foo', conf)

    def test_equality(self):
        """
        Just like a dict, __eq__ should work as expected.
        """
        conf = config.Config()

        self.assertEqual(conf, {})

        conf['foo'] = 'bar'

        self.assertEqual(conf, {'foo': 'bar'})

    def test_get_default(self):
        """
        If the key is missing, the default must be returned.
        """
        conf = config.Config()

        self.assertIsNone(conf.get('foo'))

        obj = object()

        self.assertIs(
            conf.get('foo', default=obj),
            obj
        )


class SetValueTestCase(unittest.TestCase):
    """
    Tests for `config.set_value`.
    """

    def test_set_value(self):
        """
        Set nested values using dot notation.
        """
        d = {
            'http': {
                'address': '127.0.0.1'
            }
        }

        config.set_value(d, 'http.port', 5000)
        config.set_value(d, 'log_level', 'debug')

        expected = {
            'http': {
                'address': '127.0.0.1',
                'port': 5000
            },
            'log_level': 'debug'
        }

        self.assertEqual(d, expected)

    def test_missing_key_in_dot_path(self):
        """
        A missing key in the dot notation path must raise a `KeyError`.
        """
        d = {}

        with self.assertRaises(KeyError):
            config.set_value(d, 'foo.bar', 'pies')

    def test_set_dotted_non_dict(self):
        """
        Setting a value on an object that doesn't implement `__setitem__` must
        raise a `TypeError`.
        """
        d = {
            'foo': {
                'bar': []
            }
        }

        with self.assertRaises(TypeError):
            config.set_value(d, 'foo.bar.baz', 'pies')
