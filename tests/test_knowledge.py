import pytest

from permitflow.knowledge import MemoryKnowledgeRepository
from permitflow.models import PermissionItem, Validity


@pytest.fixture
def repo():
    options = [Validity.ONE_MONTH, Validity.THREE_MONTHS]
    return MemoryKnowledgeRepository(
        [
            PermissionItem(
                name="GitHub 仓库写权限",
                category="GitHub",
                jira_project_key="ACCESS",
                approver_group="owners",
                required_fields=["repository", "reason"],
                validity_options=options,
                aliases=["github写权限", "repo write"],
            ),
            PermissionItem(
                name="Grafana 面板查看权限",
                category="监控",
                jira_project_key="ACCESS",
                approver_group="owners",
                required_fields=["dashboard", "reason"],
                validity_options=options,
                aliases=["监控面板"],
            ),
        ]
    )


async def test_alias_exact_match_is_preferred(repo):
    results = await repo.search("我需要 github写权限")
    assert [item.name for item in results] == ["GitHub 仓库写权限"]


async def test_fuzzy_search_returns_candidates(repo):
    results = await repo.search("想看监控")
    assert [item.name for item in results] == ["Grafana 面板查看权限"]
