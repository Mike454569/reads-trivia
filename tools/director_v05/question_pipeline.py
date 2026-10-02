"""One-call universal question pipeline: compile -> assemble -> QA."""
from __future__ import annotations
from .chain_compiler import compile_chain
from .question_assembler import assemble
from .final_qa import assert_playable

def build_question(chain,mechanic,*,answer_label,labels=None,difficulty_band=None,
                   clue_stats=None,current_season=None,correct_candidate=None,
                   distractor_candidates=(),all_correct_ids=(),recent_distractor_ids=(),
                   valid_answer_ids=None,recent_question_ids=(),recent_answer_ids=(),
                   as_of_season=None,retrospective=True):
    compiled=compile_chain(
        chain,mechanic,difficulty_band=difficulty_band,clue_stats=clue_stats,
        current_season=current_season,correct_candidate=correct_candidate,
        distractor_candidates=distractor_candidates,all_correct_ids=all_correct_ids,
        recent_distractor_ids=recent_distractor_ids)
    q=assemble(compiled,answer_label=answer_label,labels=labels,
               as_of_season=as_of_season,retrospective=retrospective)
    return assert_playable(
        q,valid_answer_ids=valid_answer_ids,
        recent_question_ids=recent_question_ids,recent_answer_ids=recent_answer_ids)
