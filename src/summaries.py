import pandas as pd

def build_summaries(all_sales_df: pd.DataFrame, leads_df: pd.DataFrame, camp_spend: pd.DataFrame, adset_spend: pd.DataFrame, ad_spend: pd.DataFrame):
    """Build the Campaign, Ad Set, and Ad Creative summary dataframes."""
    
    def agg_level(level_cols, spend_df):
        if all_sales_df.empty and spend_df.empty:
            return pd.DataFrame(columns=level_cols + ['Spend', 'Leads', 'CPL', 'Sales', 'Conversion Rate %', 'Revenue', 'Profit', 'ROAS', 'ROI %', 'CAC', 'Profitable?'])
            
        if spend_df.empty:
            spend_df = pd.DataFrame(columns=level_cols + ['Amount Spent'])
        
        # Aggregate sales metrics
        # Only include sales that have valid matching at this level or below
        valid_sales = all_sales_df.dropna(subset=level_cols)
        if valid_sales.empty:
            sales_agg = pd.DataFrame(columns=level_cols + ['Sales', 'Revenue', 'Attributed_Spend'])
        else:
            sales_agg = valid_sales.groupby(level_cols).agg(
                Sales=('sale_id', 'count'),
                Revenue=('total_revenue', 'sum'),
                Attributed_Spend=('attributed_spend', 'sum')
            ).reset_index()
            sales_agg['Profit'] = sales_agg['Revenue'] - sales_agg['Attributed_Spend']
            
        # Aggregate leads (if available)
        if not leads_df.empty and set(level_cols).issubset(leads_df.columns):
            valid_leads = leads_df.dropna(subset=level_cols)
            leads_agg = valid_leads.groupby(level_cols).size().reset_index(name='Leads')
            
            # Calculate standalone registration revenue
            # Filter leads not in all_sales_df
            if not all_sales_df.empty and 'email' in all_sales_df.columns and 'email' in valid_leads.columns:
                standalone_leads = valid_leads[~valid_leads['email'].isin(all_sales_df['email'])].copy()
            else:
                standalone_leads = valid_leads.copy()
                
            def get_fee(row):
                wt = str(row.get('webinar_type', '')).lower()
                fee = row.get('registration_fee', 0)
                try:
                    fee = float(fee) if pd.notna(fee) else 0.0
                except ValueError:
                    fee = 0.0
                return fee if ('paid' in wt or fee > 0) else 0.0
                
            standalone_leads['reg_revenue'] = standalone_leads.apply(get_fee, axis=1)
            reg_agg = standalone_leads.groupby(level_cols)['reg_revenue'].sum().reset_index()
            leads_agg = pd.merge(leads_agg, reg_agg, on=level_cols, how='left')
        else:
            leads_agg = pd.DataFrame(columns=level_cols + ['Leads', 'reg_revenue'])
            
        # Merge all
        res = pd.merge(spend_df, sales_agg, on=level_cols, how='outer')
        res = pd.merge(res, leads_agg, on=level_cols, how='outer')
        
        # Replace NaN with 0
        res = res.fillna({
            'Amount Spent': 0.0, 'Sales': 0, 'Revenue': 0.0, 'Attributed_Spend': 0.0, 'Profit': 0.0, 'Leads': 0, 'reg_revenue': 0.0
        })
        
        # Add standalone registration revenue to total Revenue
        res['Revenue'] = res['Revenue'] + res['reg_revenue']
        
        # Compute Profit again in case it was missing for sales without spend
        res['Profit'] = res['Revenue'] - res['Attributed_Spend']
        
        # Rename spend column
        res = res.rename(columns={'Amount Spent': 'Spend'})
        
        # Calculate rates
        # Calculate rates
        res['ROAS'] = res.apply(lambda r: (r['Revenue']/r['Attributed_Spend']) if r['Attributed_Spend'] > 0 else "N/A", axis=1)
        res['ROI %'] = res.apply(lambda r: (r['Profit']/r['Attributed_Spend']*100) if r['Attributed_Spend'] > 0 else "N/A", axis=1)
        res['CPL'] = res.apply(lambda r: (r['Spend']/r['Leads']) if r['Leads'] > 0 else "N/A", axis=1)
        res['CAC'] = res.apply(lambda r: (r['Attributed_Spend']/r['Sales']) if (r['Attributed_Spend'] > 0 and r['Sales'] > 0) else "N/A", axis=1)
        res['Conversion Rate %'] = res.apply(lambda r: (r['Sales']/r['Leads']*100) if r['Leads'] > 0 else "N/A", axis=1)
        res['Profitable?'] = res['Profit'].apply(lambda p: 'YES' if p > 0 else 'NO')
        
        # Construct Node Name depending on level
        if len(level_cols) == 1:
            res['Node Name'] = res[level_cols[0]]
        elif len(level_cols) == 2:
            res['Node Name'] = res[level_cols[0]] + ' > ' + res[level_cols[1]]
        elif len(level_cols) == 3:
            res['Node Name'] = res[level_cols[0]] + ' > ' + res[level_cols[1]] + ' > ' + res[level_cols[2]]
            
        res['Ad Account'] = 'Primary' # Mock, would need account mapping
            
        # Rearrange columns
        cols = ['Node Name', 'Ad Account', 'Spend', 'Leads', 'CPL', 'Sales', 'Conversion Rate %', 'Revenue', 'Profit', 'ROAS', 'ROI %', 'CAC', 'Profitable?']
        return res[cols]

    camp_summary = agg_level(['camp_norm'], camp_spend)
    if not camp_summary.empty:
        camp_summary = camp_summary.sort_values(by='Sales', ascending=False)
        
    adset_summary = agg_level(['camp_norm', 'adset_norm'], adset_spend)
    ad_summary = agg_level(['camp_norm', 'adset_norm', 'ad_norm'], ad_spend)
    
    return camp_summary, adset_summary, ad_summary
