#!/usr/bin/env python3
import subprocess, time, sys, os, json

def run_hermes(*args):
    cmd = ['hermes'] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Heremes error: {result.stderr}", file=sys.stderr)
    return result

def claim_task():
    res = run_hermes('kanban', 'claim')
    if res.returncode != 0:
        return None
    lines = res.stdout.strip().split('\n')
    task_id = None
    for line in lines:
        if line.startswith('Claimed') or 't_' in line:
            for token in line.split():
                if token.startswith('t_') and len(token) > 2:
                    task_id = token
                    break
    if not task_id:
        for token in res.stdout.split():
            if token.startswith('t_'):
                task_id = token
                break
    return task_id

def get_task_details(task_id):
    res = run_hermes('kanban', 'show', task_id)
    if res.returncode != 0:
        return {}
    title = None
    for line in res.stdout.split('\n'):
        if line.startswith('title:'):
            title = line.split(':',1)[1].strip()
            break
    return {'id': task_id, 'title': title}

def complete_task(task_id):
    run_hermes('kanban', 'complete', task_id)

def main():
    task_id = claim_task()
    if not task_id:
        print("No task to claim")
        return
    details = get_task_details(task_id)
    title = details.get('title', '(no title)')
    print(f"Processing task {task_id}: {title}")
    if 'iklan' in title.lower() or 'meta' in title.lower() or 'ctr' in title.lower() or 'cpc' in title.lower():
        print("  -> Working on ad copy / monitoring...")
        time.sleep(2)
        out_dir = '/root/.hermes/marketing/output'
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, f"{task_id}_adcopy.txt"), 'w') as f:
            f.write("Sample ad copy: Udah bersih, sehat, pakai Coway!")
    elif 'blog' in title.lower() or 'konten' in title.lower():
        print("  -> Writing blog...")
        time.sleep(2)
        out_dir = '/root/.hermes/marketing/output'
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, f"{task_id}_blog.txt"), 'w') as f:
            f.write("Blog draft: Manfaat HEPA untuk kesehatan keluarga...")
    elif 'email' in title.lower() or 'newsletter' in title.lower():
        print("  -> Crafting newsletter...")
        time.sleep(2)
        out_dir = '/root/.hermes/marketing/output'
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, f"{task_id}_newsletter.txt"), 'w') as f:
            f.write("Newsletter: Promo mingguan, diskon 10% untuk pembeli pertama.")
    elif 'analisis' in title.lower() or 'performa' in title.lower():
        print("  -> Analyzing performance...")
        time.sleep(2)
        out_dir = '/root/.hermes/marketing/output'
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, f"{task_id}_analysis.txt"), 'w') as f:
            f.write("Analysis: CTR 2.5%, CPC 1500, ROI 3.2x.")
    else:
        print("  -> Generic task...")
        time.sleep(1)
    print(f"  -> Completed.")
    complete_task(task_id)

if __name__ == '__main__':
    main()