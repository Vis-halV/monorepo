import pytest

from monorepo.mcp.tools.query import validate_readonly_sql


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT email FROM public.users",
        "SELECT id, email FROM users WHERE id > 10",
        "SELECT COUNT(*) FROM users",
        "SELECT email FROM users UNION SELECT email FROM users",
        "WITH active_users AS (SELECT id FROM users) "
        "SELECT id FROM active_users",
    ],
)
def test_accepts_readonly_select_queries(sql):
    assert validate_readonly_sql(sql) == sql


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "   ",
        "SELECT FROM",
        "SELECT email FROM users; SELECT id FROM users",
        "INSERT INTO users (email) VALUES ('test@example.com')",
        "UPDATE users SET email = 'test@example.com'",
        "DELETE FROM users",
        "CREATE TABLE unsafe_table (id integer)",
        "DROP TABLE users",
        "WITH removed AS (DELETE FROM users RETURNING id) "
        "SELECT id FROM removed",
        "SELECT email INTO unsafe_table FROM users",
        "SELECT email FROM users FOR UPDATE",
    ],
)
def test_rejects_invalid_or_prohibited_queries(sql):
    with pytest.raises(ValueError):
        validate_readonly_sql(sql)
