import argparse
import difflib
import sys
from termcolor import colored
from datasets import load_dataset

# Import and activate the SSL bypass from bypass.py
# This must be in the same directory
import bypass
bypass.enable_ssl_bypass()

# ==========================================
#           ARGUMENT PARSING
# ==========================================
def parse_arguments():
    parser = argparse.ArgumentParser(description="SQuAD Adversarial Dataset Diff & Stats Analysis")
    
    parser.add_argument(
        '--dataset', 
        type=str, 
        default='AddSent', 
        choices=['AddSent', 'AddOneSent'],
        help="Choose the adversarial configuration (default: AddSent)"
    )
    
    parser.add_argument(
        '--samples', 
        type=int, 
        default=5, 
        help="Number of diff samples to print in the console (default: 5)"
    )
    
    return parser.parse_args()

# ==========================================
#           MAIN SCRIPT
# ==========================================
if __name__ == "__main__":
    args = parse_arguments()
    
    DATASET_CONFIG = args.dataset
    MAX_DIFF_SAMPLES = args.samples

    print(colored(f"Configuration: Dataset={DATASET_CONFIG}, Max Samples={MAX_DIFF_SAMPLES}", "magenta"))

    # --- Load Datasets ---
    print(colored(f"Loading Original SQuAD and Adversarial SQuAD ({DATASET_CONFIG})...", "cyan"))

    original_squad = load_dataset('squad', split='validation')
    adversarial_squad = load_dataset(
        'stanfordnlp/squad_adversarial', 
        DATASET_CONFIG, 
        split='validation', 
        trust_remote_code=True
    )

    # --- Indexing Original Data ---
    print(colored("Building index...", "cyan"))
    original_map = {ex['id']: ex for ex in original_squad}

    # --- Helper Function: Highlight Differences ---
    def get_colored_diff(original_text, adversarial_text):
        matcher = difflib.SequenceMatcher(None, original_text, adversarial_text)
        output = []
        is_identical = True
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                output.append(adversarial_text[j1:j2])
            elif tag == 'insert':
                is_identical = False
                output.append(colored(adversarial_text[j1:j2], 'green', attrs=['bold']))
            elif tag == 'replace':
                is_identical = False
                output.append(colored(adversarial_text[j1:j2], 'green', attrs=['bold']))
                
        return "".join(output), is_identical

    # --- Main Loop ---
    stats = {
        "total": 0,
        "context_changed": 0,
        "question_changed": 0,
        "fully_identical": 0,
        "id_has_suffix": 0
    }

    printed_samples_count = 0

    if MAX_DIFF_SAMPLES > 0:
        print(colored(f"\nScanning dataset and printing first {MAX_DIFF_SAMPLES} differences...\n", "yellow"))

    for adv_ex in adversarial_squad:
        stats["total"] += 1
        adv_id = adv_ex['id']
        
        if '-' in adv_id:
            stats["id_has_suffix"] += 1
            
        base_id = adv_id.split('-')[0]
        
        if base_id in original_map:
            orig_ex = original_map[base_id]
            
            c_changed = (orig_ex['context'] != adv_ex['context'])
            if c_changed:
                stats["context_changed"] += 1
                
            q_changed = (orig_ex['question'] != adv_ex['question'])
            if q_changed:
                stats["question_changed"] += 1
                
            if not c_changed and not q_changed:
                stats["fully_identical"] += 1
                
            if printed_samples_count < MAX_DIFF_SAMPLES and (c_changed or q_changed):
                diff_context_text, _ = get_colored_diff(orig_ex['context'], adv_ex['context'])
                diff_question_text, _ = get_colored_diff(orig_ex['question'], adv_ex['question'])

                print(f"ID: {base_id} (Adversarial Suffix: {adv_id.replace(base_id, '')})")
                
                q_label = "Question (Modified)" if q_changed else "Question (Identical)"
                q_color = "red" if q_changed else "blue"
                print(f"{colored(q_label, q_color, attrs=['bold'])}: {diff_question_text}")
                
                print(f"{colored('Context Diff', 'white', attrs=['bold'])}:")
                snippet_len = 400
                if len(diff_context_text) > snippet_len:
                    print("..." + diff_context_text[-snippet_len:])
                else:
                    print(diff_context_text)
                    
                print("-" * 80 + "\n")
                printed_samples_count += 1

    # --- Final Report ---
    print("\n" + "="*60)
    print(colored("Full Dataset Statistics Report", "white", attrs=['bold']))
    print("="*60)
    print(f"Dataset Configuration:      {colored(DATASET_CONFIG, 'cyan')}")
    print(f"Total Adversarial Samples:  {stats['total']}")
    print("-" * 60)
    print(f"1. Context Modified:        {colored(stats['context_changed'], 'green')}   ({stats['context_changed']/stats['total']:.1%})")
    print(f"2. Question Modified:       {colored(stats['question_changed'], 'red')}     ({stats['question_changed']/stats['total']:.1%})")
    print(f"3. Completely Identical:    {colored(stats['fully_identical'], 'yellow')}   ({stats['fully_identical']/stats['total']:.1%})")
    print("-" * 60)
    print(f"4. IDs with Suffix:         {stats['id_has_suffix']}      ({stats['id_has_suffix']/stats['total']:.1%})")
    print("="*60)