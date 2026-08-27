import pandas as pd

def build_summaries(all_sales_df: pd.DataFrame, leads_df: pd.DataFrame, camp_spend: pd.DataFrame, adset_spend: pd.DataFrame, ad_spend: pd.DataFrame, placement_spend: pd.DataFrame, settings: dict = None):
    """Build the Campaign, Ad Set, Ad Creative, and Placement summary dataframes using Golden Methodology."""
    
    fallback_price = float(settings.get('fallback_price', 8999.0)) if settings else 8999.0
    
    def agg_level(level_cols, spend_df):
        if all_sales_df.empty and spend_df.empty:
            return pd.DataFrame(columns=level_cols + ['Spend', 'Leads', 'CPL', 'Sales', 'Conversion Rate %', 'Revenue', 'Profit', 'ROAS', 'ROI %', 'CAC', 'Profitable?'])
            
        if spend_df.empty:
            spend_df = pd.DataFrame(columns=level_cols + ['Amount Spent'])
        else:
            for col in level_cols:
                if col in spend_df.columns:
                    spend_df = spend_df[~spend_df[col].isin(['', 'Unattributed', 'unattributed'])]
        
        # Aggregate sales metrics
        valid_sales = all_sales_df.dropna(subset=level_cols).copy()
        for col in level_cols:
            valid_sales = valid_sales[~valid_sales[col].isin(['', 'Unattributed', 'unattributed'])]
        if valid_sales.empty:
            sales_agg = pd.DataFrame(columns=level_cols + ['Sales'])
        else:
            sales_agg = valid_sales.groupby(level_cols).agg(
                Sales=('sale_id', 'count')
            ).reset_index()
            
        # Aggregate leads
        if not leads_df.empty and set(level_cols).issubset(leads_df.columns):
            valid_leads = leads_df.dropna(subset=level_cols).copy()
            for col in level_cols:
                valid_leads = valid_leads[~valid_leads[col].isin(['', 'Unattributed', 'unattributed'])]
            leads_agg = valid_leads.groupby(level_cols).size().reset_index(name='Leads')
        else:
            leads_agg = pd.DataFrame(columns=level_cols + ['Leads'])
            
        # Merge all
        res = pd.merge(spend_df, sales_agg, on=level_cols, how='outer')
        res = pd.merge(res, leads_agg, on=level_cols, how='outer')
        
        # Replace NaN with 0
        res = res.fillna({
            'Amount Spent': 0.0, 'Sales': 0, 'Leads': 0
        })
        
        # Golden Methodology Revenue Calculation
        res['Revenue'] = res['Sales'] * fallback_price
        
        # Rename spend column
        res = res.rename(columns={'Amount Spent': 'Spend'})
        
        # Compute Profit (Golden Methodology: Revenue - Spend)
        res['Profit'] = res['Revenue'] - res['Spend']
        
        # Calculate rates
        res['ROAS'] = res.apply(lambda r: (r['Revenue']/r['Spend']) if r['Spend'] > 0 else "N/A", axis=1)
        res['ROI %'] = res.apply(lambda r: (r['Profit']/r['Spend']*100) if r['Spend'] > 0 else "N/A", axis=1)
        res['CPL'] = res.apply(lambda r: (r['Spend']/r['Leads']) if r['Leads'] > 0 else "N/A", axis=1)
        res['CAC'] = res.apply(lambda r: (r['Spend']/r['Sales']) if (r['Spend'] > 0 and r['Sales'] > 0) else "N/A", axis=1)
        res['Conversion Rate %'] = res.apply(lambda r: (r['Sales']/r['Leads']*100) if r['Leads'] > 0 else "N/A", axis=1)
        res['Profitable?'] = res['Profit'].apply(lambda p: 'YES' if p > 0 else 'NO')
        
        # Construct Node Name depending on level
        if len(level_cols) == 1:
            res['Node Name'] = res[level_cols[0]]
        elif len(level_cols) == 2:
            res['Node Name'] = res[level_cols[0]] + ' > ' + res[level_cols[1]]
        elif len(level_cols) == 3:
            res['Node Name'] = res[level_cols[0]] + ' > ' + res[level_cols[1]] + ' > ' + res[level_cols[2]]
            
        res['Ad Account'] = 'Primary'
            
        # Rearrange columns
        cols = ['Node Name', 'Ad Account', 'Spend', 'Leads', 'CPL', 'Sales', 'Conversion Rate %', 'Revenue', 'Profit', 'ROAS', 'ROI %', 'CAC', 'Profitable?']
        return res[cols]

    camp_summary = agg_level(['camp_norm'], camp_spend)
    if not camp_summary.empty:
        camp_summary = camp_summary.sort_values(by='Sales', ascending=False)
        
    adset_summary = agg_level(['camp_norm', 'adset_norm'], adset_spend)
    ad_summary = agg_level(['camp_norm', 'adset_norm', 'ad_norm'], ad_spend)
    placement_summary = agg_level(['camp_norm', 'placement_norm'], placement_spend)
    
    # NOW FORMAT CAMPAIGN SUMMARY ONLY
    if not camp_summary.empty:
        camp_summary['Campaign Name'] = camp_summary['Node Name']
        camp_summary['Total Leads'] = camp_summary['Leads']
        camp_summary['Total Sales'] = camp_summary['Sales']
        camp_summary['Attributed Sales'] = camp_summary['Sales']
        camp_summary['Total Revenue'] = camp_summary['Revenue']
        camp_summary['Raw Meta Spend'] = camp_summary['Spend']
        camp_summary['Spend / Cost'] = camp_summary['Spend']
        camp_summary['Conversion Rate'] = camp_summary['Conversion Rate %']
        camp_summary['ROI'] = camp_summary['ROI %']
        camp_summary['Price Per Sale'] = fallback_price
        camp_summary['Funnel Type'] = settings.get('funnel_type', 'Paid') if settings else 'Paid'
        
        c_cols = ['Campaign Name', 'Total Leads', 'Total Sales', 'Attributed Sales', 'Total Revenue', 'Raw Meta Spend', 'Spend / Cost', 'CPL', 'CAC', 'ROAS', 'ROI', 'Conversion Rate', 'Profit', 'Price Per Sale', 'Funnel Type']
        camp_summary = camp_summary[c_cols]
    else:
        camp_summary = pd.DataFrame(columns=['Campaign Name', 'Total Leads', 'Total Sales', 'Attributed Sales', 'Total Revenue', 'Raw Meta Spend', 'Spend / Cost', 'CPL', 'CAC', 'ROAS', 'ROI', 'Conversion Rate', 'Profit', 'Price Per Sale', 'Funnel Type'])
        
    return camp_summary, adset_summary, ad_summary, placement_summary
