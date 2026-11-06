"""Descriptive, coverage-aware comparisons of filtered runs."""

from dataclasses import dataclass, replace
from statistics import mean, median

from labels import matches, run_labels
from metrics import Filters, filter_dataset, summarize
from runs import calculate_run


@dataclass(frozen=True)
class Group:
    """Named group whose filters intersect the global filters."""

    name: str
    filters: Filters


@dataclass(frozen=True)
class Measure:
    """Value with eligible and total run counts and provenance."""

    value: float | None
    eligible: int
    total: int
    provenance: str


@dataclass(frozen=True)
class GroupResult:
    """Comparison measures, eligible distributions and recorded conditions."""

    name: str
    run_ids: tuple[str, ...]
    measures: dict[str, Measure]
    distribution: tuple[tuple[str, float], ...]
    conditions: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class Difference:
    """Difference from the first group's baseline, with undefined percentage retained."""

    absolute: float | None
    percentage: float | None


@dataclass(frozen=True)
class Comparison:
    """Descriptive group results, baseline differences and caveats."""

    groups: tuple[GroupResult, ...]
    differences: dict[str, dict[str, Difference]]
    overlapping_runs: dict[str, tuple[str, ...]]
    condition_flags: tuple[str, ...]
    caveats: tuple[str, ...]


def _manual_match(data, run, selection):
    explicit, inherited = run_labels(data, run)
    return matches(data, explicit | inherited, selection.label_ids, selection.label_mode,
                   selection.task_types, selection.execution_modes, run)


def _without_manual(selection):
    return replace(selection, label_ids=None, task_types=None, execution_modes=None)


def _has_observation_filters(selection):
    return any(value is not None for value in (selection.start_date, selection.end_date,
               selection.projects, selection.models, selection.agent_roles))


def _measure(values, total, provenance, reducer=mean):
    return Measure(reducer(values) if values else None, len(values), total, provenance)


def compare_groups(groups, data, events, increments, frame, global_filters=Filters()):
    """Compare two or more groups against the first group, descriptively.

    Each group is the intersection of its own filters and global filters.
    Runs with missing sources remain in unfiltered groups as unknown; an
    observation-dependent filter excludes them because it cannot match them.
    """
    if len(groups) < 2 or any(not isinstance(g.name, str) or not g.name.strip() for g in groups):
        raise ValueError("At least two named groups are required.")
    if len({g.name.casefold() for g in groups}) != len(groups):
        raise ValueError("Group names must be unique.")
    results = []
    for group in groups:
        base = filter_dataset(filter_dataset(frame, _without_manual(global_filters)), _without_manual(group.filters))
        run_records = []
        for run in data["runs"]:
            if not _manual_match(data, run, global_filters) or not _manual_match(data, run, group.filters):
                continue
            if any(selection.sessions is not None and run["session_id"] not in selection.sessions
                   for selection in (global_filters, group.filters)):
                continue
            result = calculate_run(run, events, increments)
            references = set(result.event_references) | {item.reference for item in result.increments}
            selected = base.loc[(base["session"] == run["session_id"]) & base["reference"].isin(references)].copy()
            if selected.empty and (references or _has_observation_filters(global_filters) or _has_observation_filters(group.filters)):
                continue
            selected.attrs["run_filter"] = True
            summary = summarize(selected, events)
            full_event_coverage = bool(result.event_references) and set(result.event_references) <= set(selected["reference"])
            run_records.append((run, result, selected, summary, full_event_coverage))
        count = len(run_records)
        token_values = [r[3].totals["total_tokens"].value for r in run_records if r[3].totals["total_tokens"].value is not None]
        output_values = [r[3].totals["output_tokens"].value for r in run_records if r[3].totals["output_tokens"].value is not None]
        duration_values = [r[1].elapsed_seconds for r in run_records if r[4] and r[1].elapsed_seconds is not None]
        outcomes = [r[0].get("outcome", "unknown") for r in run_records if r[0].get("outcome", "unknown") in ("success", "failure")]
        scores = [r[0]["evaluation_score"] for r in run_records if r[0].get("evaluation_score") is not None]
        pairs = []
        for _, _, selected, _, _ in run_records:
            eligible = [increment for increment in selected["increment"] if increment is not None
                        and increment.values.get("input_tokens") is not None
                        and increment.values.get("cached_input_tokens") is not None]
            input_sum = sum(increment.values["input_tokens"] for increment in eligible)
            if input_sum > 0:
                pairs.append((input_sum, sum(increment.values["cached_input_tokens"] for increment in eligible)))
        denominator = sum(item[0] for item in pairs)
        measures = {
            "mean_tokens": _measure(token_values, count, "root-thread counters; partial/estimated"),
            "median_tokens": _measure(token_values, count, "root-thread counters; partial/estimated", median),
            "output_tokens": _measure(output_values, count, "mean root-thread output tokens per eligible run; partial/estimated"),
            "cache_percentage": Measure(100 * sum(item[1] for item in pairs) / denominator if denominator else None,
                                        len(pairs), count, "weighted eligible cached/input totals; partial/estimated"),
            "subagent_share": Measure(None, 0, count, "unknown: root-only usage and unresolved parent scope"),
            "elapsed_seconds": _measure(duration_values, count, "observed or manual spans; not verified execution duration"),
            "success_rate": Measure(100 * outcomes.count("success") / len(outcomes) if outcomes else None,
                                    len(outcomes), count, "manual success/failure only; partial and unknown excluded"),
            "evaluation_score": _measure(scores, count, "manual evaluation scores"),
        }
        conditions = {}
        definitions = {item["id"]: item for item in data["labels"]}
        for field in ("task_type", "execution_mode"):
            values = set()
            for run, _, _, _, _ in run_records:
                direct = run.get(field)
                if direct:
                    values.add(direct)
                else:
                    explicit, inherited = run_labels(data, run)
                    recorded = {definitions[label].get("value") for label in explicit | inherited
                                if label in definitions and definitions[label].get("key", "").casefold() == field}
                    values.update(value for value in recorded if value)
                    if not recorded:
                        values.add("Unknown")
            conditions[field] = tuple(sorted(values))
        models = set()
        for _, _, selected, _, _ in run_records:
            models.update(str(value) for value in selected["model"].dropna().unique())
            if selected["model"].isna().any() or selected.empty:
                models.add("Unknown")
        conditions["model"] = tuple(sorted(models))
        distribution = tuple((r[0]["id"], r[3].totals["total_tokens"].value) for r in run_records
                             if r[3].totals["total_tokens"].value is not None)
        results.append(GroupResult(group.name, tuple(r[0]["id"] for r in run_records), measures, distribution, conditions))
    overlaps = {}
    for index, left in enumerate(results):
        for right in results[index + 1:]:
            shared = tuple(sorted(set(left.run_ids) & set(right.run_ids)))
            if shared:
                overlaps[f"{left.name} / {right.name}"] = shared
    flags = tuple(f"Groups differ in recorded {field}; unknown values are shown explicitly."
                  for field in ("task_type", "execution_mode", "model")
                  if len({result.conditions[field] for result in results}) > 1)
    differences = {}
    for result in results[1:]:
        differences[result.name] = {}
        for metric in ("mean_tokens", "median_tokens", "output_tokens", "elapsed_seconds"):
            baseline, value = results[0].measures[metric].value, result.measures[metric].value
            delta = value - baseline if baseline is not None and value is not None else None
            differences[result.name][metric] = Difference(delta, 100 * delta / baseline if delta is not None and baseline != 0 else None)
    return Comparison(tuple(results), differences, overlaps, flags,
                      ("Descriptive differences do not establish causation.",
                       "Run token totals are root-thread-only and may be partial or estimated; child usage is excluded.",
                       "Elapsed spans are not verified execution duration."))



