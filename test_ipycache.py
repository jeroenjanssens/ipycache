# -*- coding: utf-8 -*-
"""Tests for ipycache.
"""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------
import os
import sys
from cStringIO import StringIO
from nose.tools import raises, assert_raises
from ipycache import (save_vars, load_vars, clean_var, clean_vars, do_save, 
    cache, exec_, conditional_eval)


#------------------------------------------------------------------------------
# Functions tests
#------------------------------------------------------------------------------
def test_conditional_eval():
    test_var = 'abc'
    assert conditional_eval('$test_var', locals()) == 'abc'

def test_clean_var():
    assert clean_var('abc') == 'abc'
    assert clean_var('abc ') == 'abc'
    assert clean_var('abc,') == 'abc'
    assert clean_var(',abc') == 'abc'
    
def test_clean_vars():
    assert clean_vars(['abc', 'abc,']) == ['abc'] * 2

def test_do_save():
    path = 'myvars.pkl'
    
    # File exists.
    open(path, 'wb').close()
    assert_raises(ValueError, do_save, path, force=True, read=True)
    assert do_save(path, force=True, read=False)
    assert not do_save(path, force=False, read=False)
    assert not do_save(path, force=False, read=True)
    os.remove(path)
    
    # File does not exist.
    assert_raises(ValueError, do_save, path, force=True, read=True)
    assert do_save(path, force=True, read=False)
    assert do_save(path, force=False, read=False)
    assert not do_save(path, force=False, read=True)
    
@raises(IOError)
def test_load_fail():
    path = 'myvars.pkl'
    load_vars(path, ['a', 'b'])

def test_save_load():
    path = 'myvars.pkl'
    vars = {'a': 1, 'b': '2'}
    save_vars(path, vars)
    vars2 = load_vars(path, list(vars.keys()))
    assert vars == vars2
    
    os.remove(path)
    

#------------------------------------------------------------------------------
# Cache magic tests
#------------------------------------------------------------------------------
def test_cache_1():
    path = 'myvars.pkl'
    cell = """a = 1"""
    
    user_ns = {}
    def ip_run_cell(cell):
        exec_(cell, {}, user_ns)
    
    def ip_push(vars):
        user_ns.update(vars)
    
    cache(cell, path, vars=['a'], force=False, read=False,
          ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
    assert user_ns['a'] == 1
    
    # We modify the variable in the namespace,
    user_ns['a'] = 2
    # and execute the cell again. The value should be loaded from the pickle
    # file.
    cache("""a = 2""", path, vars=['a'], force=False, read=False,
          ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
    assert user_ns['a'] == 1
    
    # Now, we force the cell's execution.
    cache("""a = 2""", path, vars=['a'], force=True, read=False,
          ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
    assert user_ns['a'] == 2
    
    # Now, we prevent the cell's execution.
    user_ns['a'] = 0
    cache("""a = 3""", path, vars=['a'], force=False, read=True,
          ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
    assert user_ns['a'] == 2
    
    os.remove(path)
    
def test_cache_exception():
    """Check that, if an exception is raised during the cell's execution,
    the pickle file is not written."""
    path = 'myvars.pkl'
    cell = """a = 1;b = 1/0"""
    
    user_ns = {}
    def ip_run_cell(cell):
        exec_(cell, {}, user_ns)
    
    def ip_push(vars):
        user_ns.update(vars)
    
    cache(cell, path, vars=['a'], force=False, read=False,
          ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
    assert user_ns['a'] == 1
    
    assert not os.path.exists(path), os.remove(path)
    
def test_cache_outputs():
    """Test the capture of stdout."""
    path = 'myvars.pkl'
    cell = """a = 1;print(a+1)"""
    
    user_ns = {}
    def ip_run_cell(cell):
        exec_(cell, {}, user_ns)
    
    def ip_push(vars):
        user_ns.update(vars)
    
    cache(cell, path, vars=['a'], verbose=False,
          ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
    assert user_ns['a'] == 1
    
    # Capture stdout.
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    user_ns = {}
    cache(cell, path, vars=['a'], verbose=False,
          ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
    assert user_ns['a'] == 1
    
    sys.stdout = old_stdout
    
    # Check that stdout contains the print statement of the cached cell.
    assert mystdout.getvalue() == '2\n'
    
    os.remove(path)

@raises(ValueError)
def test_cache_fail_1():
    """Fails when saving inexistent variables."""
    path = 'myvars.pkl'
    cell = """a = 1"""
    
    user_ns = {}
    def ip_run_cell(cell):
        exec_(cell, {}, user_ns)
    
    def ip_push(vars):
        user_ns.update(vars)
    
    cache(cell, path, vars=['a', 'b'],
          ip_user_ns=user_ns, ip_run_cell=ip_run_cell, ip_push=ip_push)
    
    os.remove(path)
