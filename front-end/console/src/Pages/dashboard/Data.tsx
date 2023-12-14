export interface success_record
{
  receive_time: string;
  ftime: string;
  exec_status: string;
  job_finished_time: string;
  cluster_created_time:string;
  run_duration:string;
}
export interface failed_record
{
  receive_time: string;
  ftime: string;
  exec_status: string;
  reason: string;
}
export class Statistics {
    last_7d_failed: string = '0';
    last_7d_success: string = '0';
    last_day_success: success_record[] =[];
    last_day_failed: failed_record[] =[];

 

    constructor(initializer?: any) {
      if (!initializer) return;
      if (initializer.last_7d_failed) this.last_7d_failed = initializer.last_7d_failed;
      if (initializer.last_7d_success) this.last_7d_success = initializer.last_7d_success;
      if (initializer.last_day_success) this.last_day_success = initializer.last_day_success;
      if (initializer.last_day_failed) this.last_day_failed = initializer.last_day_failed;
    
          
    }
  }
