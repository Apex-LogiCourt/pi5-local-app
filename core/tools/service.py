from core.data_models import CaseData, Case, Profile, Evidence

def hanler_question(question: str, profile : Profile) :
    from interrogation.interrogator import it
    chain = it.build_ask_chain(question, profile)
    
    chain.strem
    
    
    