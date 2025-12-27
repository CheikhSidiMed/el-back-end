python manage.py shell

from school_app.models import Permission

def create_perm(code, label, parent=None):
    return Permission.objects.get_or_create(
        code=code,
        defaults={'label': label, 'parent': parent}
    )[0]

# Dashboard
fDashboard = create_perm('fDashboard', 'الصفحة الرئيسية')

# البيانات
fData = create_perm('fData', 'البيانات')
create_perm('fStudents', 'الطلاب', fData)
create_perm('fAgents', 'الوكلاء، الفروع و الاقسام', fData)
create_perm('fActivities', 'الدورات والأنشطة', fData)

# شؤون الطلاب
fStudentAffairs = create_perm('fStudentAffairs', 'شؤون الطلاب')
create_perm('fWeeklyFollow', 'المتابعة الأسبوعية', fStudentAffairs)
create_perm('fMonthlyReport', 'الحصيلة الشهرية', fStudentAffairs)
create_perm('fRating', 'استمارة تقييم', fStudentAffairs)
create_perm('fTehji', 'استمارة التهجي', fStudentAffairs)
create_perm('fResults', 'نتائج تقييم', fStudentAffairs)
create_perm('fAbsenceForm', 'استمارة الغياب', fStudentAffairs)
create_perm('fAbsenceManage', 'إدارة الغياب', fStudentAffairs)

# عمليات الإدخال
fInputOperations = create_perm('fInputOperations', 'عمليات الإدخال')
create_perm('fStudentPayment', 'تسديد رسوم الطلاب', fInputOperations)
create_perm('fAgentPayment', 'تسديد رسوم الوكلاء', fInputOperations)
create_perm('fTransactionAdd', 'تسجيل عملية حسابية', fInputOperations)
create_perm('fActivityPayment', 'تسجيل رسوم الإشتراكات', fInputOperations)
create_perm('fGarantPayment', 'تسجيل رسوم الكافلون', fInputOperations)

# الحسابات
fAccounts = create_perm('fAccounts', 'الحسابات')
create_perm('fAccountManagement', 'الحسابات, البنوك, الموظفين', fAccounts)
create_perm('fGarantAccounts', 'الحسابات الكافلون', fAccounts)
create_perm('fStudentAgentAccounts', 'حسابات الطلاب, والوكلاء', fAccounts)

# التقارير المالية
fFinance = create_perm('fFinance', 'التقارير المالية')
create_perm('fDaily', 'اليومية', fFinance)
create_perm('fUnpaidStudents', 'الطلاب المدينون', fFinance)
create_perm('fFreeStudents', 'الطلاب المعفيون', fFinance)
create_perm('fMonthlyFinancialReport', 'التقرير المالي الشهري', fFinance)

# الإجراءات
fProcedures = create_perm('fProcedures', 'الإجراءات')
create_perm('fSalaryPayment', 'إدخال الرواتب', fProcedures)
create_perm('fTransactionEdit', 'تعديل عملية حسابية', fProcedures)

# المستخدمون
create_perm('fUsers', 'المستخدمون')

# الإعدادات
create_perm('fSettings', 'الإعدادات')

print("✅ All permissions inserted successfully")




  allItems = [
    {
      routeLink: 'dashboard',
      icon: 'fas fa-home',
      label: 'الصفحة الرئيسية',
      permission: PERMISSIONS.fDashboard
    },
    {
      routeLink: '',
      icon: 'fas fa-user-graduate',
      label: ' البيانات',
      permission: PERMISSIONS.fData,
      subItems: [
        { routeLink: 'students', label: 'الطلاب', permission: PERMISSIONS.fStudents },
        { routeLink: 'agents', label: 'الوكلاء، الفروع و الاقسام', permission: PERMISSIONS.fAgents },
        { routeLink: 'activitys', label: 'الدورات والأنشطة', permission: PERMISSIONS.fActivities }
      ]
    },
    {
      routeLink: '',
      icon: 'fas fa-book',
      label: ' شؤون الطلاب',
      permission: PERMISSIONS.fStudentAffairs,
      subItems: [
        { routeLink: 'm_week', label: 'المتابعة الأسبوعية', permission: PERMISSIONS.fWeeklyFollow },
        { routeLink: 'h_month', label: 'الحصيلة الشهرية', permission: PERMISSIONS.fMonthlyReport },
        { routeLink: 'm_rating', label: 'استمارة تقييم', permission: PERMISSIONS.fRating },
        { routeLink: 'm_tehji', label: 'استمارة التهجي', permission: PERMISSIONS.fTehji },
        { routeLink: 'result', label: 'نتائج تقييم', permission: PERMISSIONS.fResults },
        { routeLink: 'absence', label: 'استمارة الغياب', permission: PERMISSIONS.fAbsenceForm },
        { routeLink: 'abs/add', label: 'إدارة الغياب', permission: PERMISSIONS.fAbsenceManage }
      ]
    },
    {
      routeLink: '',
      icon: 'fas fa-money-bill-wave',
      label: 'عمليات الإدخال',
      permission: PERMISSIONS.fInputOperations,
      subItems: [
        { routeLink: 'payment', label: 'تسديد رسوم الطلاب', permission: PERMISSIONS.fStudentPayment },
        { routeLink: 'agent-payment', label: 'تسديد رسوم الوكلاء', permission: PERMISSIONS.fAgentPayment },
        { routeLink: 'tran-account', label: 'تسجيل عملية حسابية', permission: PERMISSIONS.fTransactionAdd },
        { routeLink: 'activity-payment', label: 'تسجيل رسوم الإشتراكات', permission: PERMISSIONS.fActivityPayment },
        { routeLink: 'garant-payment', label: 'تسجيل رسوم الكافلون', permission: PERMISSIONS.fGarantPayment }
      ]
    },
    {
      routeLink: '',
      icon: 'fas fa-file-invoice-dollar',
      label: 'الحسابات',
      permission: PERMISSIONS.fAccounts,
      subItems: [
        { routeLink: 'account-mg', label: 'الحسابات, البنوك, الموظفين', permission: PERMISSIONS.fAccountManagement },
        { routeLink: 'garant', label: 'الحسابات الكافلون', permission: PERMISSIONS.fGarantAccounts },
        { routeLink: 'acc-student-agent', label: 'حسابات الطلاب, والوكلاء', permission: PERMISSIONS.fStudentAgentAccounts },
      ]
    },
    {
      routeLink: '',
      icon: 'fas fa-clipboard-check',
      label: 'التقارير المالية',
      permission: PERMISSIONS.fFinance,
      subItems: [
        { routeLink: 'dailly', label: 'اليومية', permission: PERMISSIONS.fDaily },
        { routeLink: 'unpaid-students', label: 'الطلاب المدينون', permission: PERMISSIONS.fUnpaidStudents },
        { routeLink: 'free-students', label: 'الطلاب المعفيون', permission: PERMISSIONS.fFreeStudents },
        { routeLink: 'monthly-financial-reports', label: 'التقرير المالي الشهري', permission: PERMISSIONS.fMonthlyFinancialReport }
      ]
    },
    {
      routeLink: '',
      icon: 'fas fa-clipboard-check',
      label: 'الإجراءات',
      permission: PERMISSIONS.fProcedures,
      subItems: [
        { routeLink: 'salary-payment', label: 'إدخال الرواتب', permission: PERMISSIONS.fSalaryPayment },
        { routeLink: 'mg-transations', label: 'تعديل عملية حسابية', permission: PERMISSIONS.fTransactionEdit },
      ]
    },
    { routeLink: 'users', icon: 'fas fa-users', label: 'المستخدمون', permission: PERMISSIONS.fUsers },
    { routeLink: 'settings', icon: 'fas fa-cog', label: 'الإعدادات', permission: PERMISSIONS.fSettings },
  ];


    userRole = 'dg_lessen';
  constructor(private router: Router, private generalService: GeneralService) {}

  ngOnInit(): void {
    this.generalService.getResource(`/api/role-permissions/${this.userRole}/`).subscribe((data) => {
      const codes = data.permissions.map((p: any) => p.code);
      this.filteredItems = this.filterMenuByPermissions(this.allItems, codes);
    });

  }


python manage.py createsuperuser