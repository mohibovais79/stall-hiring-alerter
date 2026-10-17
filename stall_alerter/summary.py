"""Bottleneck summary over the flagged list."""
from dataclasses import dataclass


@dataclass
class GroupCount:
    name: str
    count: int
    share: float
    bottleneck: bool


@dataclass
class Summary:
    owners: list
    stages: list
    total: int


def summarize(flagged, min_count=3, min_pct=0.5):
    """Count flagged candidates per owner and per stage."""
    total = len(flagged)

    def build(column):
        groups = []
        for name, count in flagged[column].value_counts().items():
            share = count / total
            groups.append(GroupCount(
                name=str(name), count=int(count), share=share,
                bottleneck=count >= min_count or share >= min_pct,
            ))
        return sorted(groups, key=lambda g: (-g.count, g.name))

    return Summary(owners=build("owner"), stages=build("stage"), total=total)
