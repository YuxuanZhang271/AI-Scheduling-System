import asyncio
from utils.scheduler_updated import Scheduler

async def test():
    try:
        sch = Scheduler('68e9212ba448a137ef81a37c')
        print("Initializing scheduler...")
        await sch.initScheduler()
        print(f'✓ Unscheduled tasks: {len(sch.unscheduled_tasks)}')
        print(f'✓ Windows: {len(sch.windows)}')
        
        print("\nArranging tasks to windows...")
        sch.arrangeTasksToWindows()
        print(f'✓ After arrange: {len(sch.unscheduled_tasks)} unscheduled')
        
        print("\nScheduling in windows...")
        sch.scheduleTasksInWindow()
        
        print("\nDistributing rest times...")
        sch.distributeRestTimes()
        
        print(f'\n✓ Tasks scheduled in windows:')
        for w_idx, w in enumerate(sch.windows):
            print(f'  Window {w_idx}: {len(w["tasks"])} tasks')
            for t in w['tasks']:
                print(f'    - {t.get("name")}: {t.get("start_time")}')
        
        print("\n✅ Scheduler test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())