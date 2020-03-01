-- Gerrit中，会对“查看Side-by-Side”进行记录，通过直接查询MySql可获取。
-- 涉及的表：changes , patch_set_approvals , account_patch_reviews
-- 查询条件：Code-Review +2的人，并且查看过Side-by-Side的记录

select distinct c.change_id,
c.current_patch_set_id patch_set,c.owner_account_id owner,
psa.account_id reviewer,c.dest_project_name project,
c.dest_branch_name branch
from changes c
left outer join patch_set_approvals as psa on (
c.change_id = psa.change_id and
c.current_patch_set_id = psa.patch_set_id and
c.owner_account_id != psa.account_id and
psa.category_id='Code-Review' and psa.value=2)
left outer join account_patch_reviews as apr on (
c.change_id = apr.change_id and
c.current_patch_set_id = apr.patch_set_id and
psa.account_id = apr.account_id)
where apr.file_name is not null and
c.owner_account_id not in (1,2,10,17,24,71) -- 这里写明不参与统计的人
c.dest_branch_name = 'refs/heads/？'; -- 这里写名统计用的分支名 
