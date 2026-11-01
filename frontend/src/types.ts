export type Row = Record<string, string | number | null>;
export type Filters = {start:string;end:string;category:string;state:string};
export type Quality = {raw_rows:number;clean_rows:number;duplicates:number;excluded_rows:number;primary_key_unique:boolean;columns:string[];missing_values:Record<string,number>;invalid_values:Record<string,number>;orphans:Record<string,number>;excluded:Record<string,number>};
export type Meta = {source:string;mode:string;start:string;end:string;ingested_at:string;categories:string[];states:string[];tables:Record<string,Quality>;checks:Record<string,number>};
export type Finding = {observation:string;interpretation:string;action:string;limitation:string};
export type Dashboard = {meta:Meta;filters:Filters;kpis:Record<string,number|null>;comparison:{start:string;end:string;complete:boolean;changes:Record<string,number|null>};monthly:Row[];categories:Row[];regions:Row[];frequency:Row[];cohorts:Row[];delivery:Row[];reviews:Row[];findings:Finding[]};
export type Metric = {name:string;formula:string;statuses:string;date:string;grain:string;exclusions:string};
